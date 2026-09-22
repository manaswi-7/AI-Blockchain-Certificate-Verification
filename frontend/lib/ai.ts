import fs from "node:fs/promises";
import path from "node:path";
import * as ort from "onnxruntime-node";
import sharp from "sharp";

let sessionPromise: Promise<ort.InferenceSession> | undefined;

const MODEL_PATH = path.join(process.cwd(), "models", "certificate_tamper_model.onnx");

async function getSession() {
  if (!sessionPromise) {
    sessionPromise = fs.readFile(MODEL_PATH).then((model) =>
      ort.InferenceSession.create(new Uint8Array(model)),
    );
  }
  return sessionPromise;
}

function toNchw(data: Buffer) {
  const out = new Float32Array(3 * 224 * 224);
  for (let y = 0; y < 224; y++) {
    for (let x = 0; x < 224; x++) {
      const pixel = (y * 224 + x) * 3;
      const pos = y * 224 + x;
      out[pos] = data[pixel];
      out[224 * 224 + pos] = data[pixel + 1];
      out[2 * 224 * 224 + pos] = data[pixel + 2];
    }
  }
  return out;
}

function toNhwc(data: Buffer) {
  return Float32Array.from(data, (value) => value);
}

export async function analyzeCertificate(bytes: ArrayBuffer) {
  const buffer = Buffer.from(bytes);
  const { data, info } = await sharp(buffer)
    .removeAlpha()
    .resize(224, 224, { fit: "fill" })
    .raw()
    .toBuffer({ resolveWithObject: true });

  if (info.channels !== 3) {
    throw new Error("Certificate image could not be converted to RGB");
  }

  const session = await getSession();
  const inputName = session.inputNames[0];
  const outputName = session.outputNames[0];
  const inputMeta = session.inputMetadata[inputName];

  if (!inputName || !outputName || !inputMeta) {
    throw new Error("AI model has no usable input/output tensors");
  }

  const shape = inputMeta.dimensions.map(Number);
  let input: Float32Array;
  let inputShape: number[];

  if (shape.length === 4 && shape[1] === 3 && shape[2] === 224 && shape[3] === 224) {
    input = toNchw(data);
    inputShape = [1, 3, 224, 224];
  } else if (shape.length === 4 && shape[1] === 224 && shape[2] === 224 && shape[3] === 3) {
    input = toNhwc(data);
    inputShape = [1, 224, 224, 3];
  } else {
    throw new Error(`Unsupported AI model input shape: ${JSON.stringify(shape)}`);
  }

  const tensor = new ort.Tensor("float32", input, inputShape);
  const result = await session.run({ [inputName]: tensor });
  const output = result[outputName] as ort.Tensor | undefined;

  if (!output?.data?.length) {
    throw new Error("AI model returned no prediction");
  }

  const probability = Number(output.data[0]);
  if (!Number.isFinite(probability)) {
    throw new Error("AI model returned an invalid prediction");
  }

  const tamperProbability = Math.max(0, Math.min(1, probability));
  const classification = tamperProbability >= 0.5 ? "TAMPERED" : "GENUINE";
  const confidence =
    classification === "TAMPERED" ? tamperProbability : 1 - tamperProbability;

  return {
    classification,
    confidence: Number(confidence.toFixed(4)),
    tamper_probability: Number(tamperProbability.toFixed(4)),
    model_available: true,
    recommendation:
      classification === "TAMPERED"
        ? "Potential visual tampering detected; continue with hash and blockchain verification."
        : "No visual tampering detected by the model; continue with hash and blockchain verification.",
  };
}
