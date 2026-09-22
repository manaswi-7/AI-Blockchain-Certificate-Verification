import fs from "node:fs/promises";
import path from "node:path";
import * as ort from "onnxruntime-node";
import sharp from "sharp";

let sessionPromise: Promise<ort.InferenceSession> | undefined;

const MODEL_PATH = path.join(process.cwd(), "models", "certificate_tamper_model.onnx");
const FALLBACK_THRESHOLD = 0.5;

async function getSession() {
  if (!sessionPromise) {
    sessionPromise = fs.readFile(MODEL_PATH).then((model) =>
      ort.InferenceSession.create(new Uint8Array(model)),
    );
  }
  return sessionPromise;
}

function numericDimension(value: number | string | null | undefined) {
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

function toNchw(data: Buffer, width: number, height: number) {
  const pixels = width * height;
  const out = new Float32Array(3 * pixels);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const pixel = (y * width + x) * 3;
      const pos = y * width + x;
      out[pos] = data[pixel];
      out[pixels + pos] = data[pixel + 1];
      out[2 * pixels + pos] = data[pixel + 2];
    }
  }

  return out;
}

function toNhwc(data: Buffer) {
  return Float32Array.from(data, (value) => value);
}

export async function analyzeCertificate(bytes: ArrayBuffer) {
  const buffer = Buffer.from(bytes);
  const session = await getSession();

  const inputName = session.inputNames[0];
  const outputName = session.outputNames[0];
  const inputMeta = inputName ? session.inputMetadata[inputName] : undefined;

  if (!inputName || !outputName || !inputMeta) {
    throw new Error("AI model has no usable input/output tensors");
  }

  const shape = inputMeta.dimensions;
  if (shape.length !== 4) {
    throw new Error(`Unsupported AI model input rank: ${JSON.stringify(shape)}`);
  }

  const dim1 = numericDimension(shape[1]);
  const dim2 = numericDimension(shape[2]);
  const dim3 = numericDimension(shape[3]);

  let width: number;
  let height: number;
  let channels: number;
  let layout: "NCHW" | "NHWC";

  if (dim1 === 3 && dim2 && dim3) {
    layout = "NCHW";
    channels = 3;
    height = dim2;
    width = dim3;
  } else if (dim1 && dim2 && dim3 === 3) {
    layout = "NHWC";
    width = dim2;
    height = dim1;
    channels = 3;
  } else {
    throw new Error(`Unsupported AI model input shape: ${JSON.stringify(shape)}`);
  }

  const { data, info } = await sharp(buffer)
    .removeAlpha()
    .resize(width, height, { fit: "fill" })
    .raw()
    .toBuffer({ resolveWithObject: true });

  if (info.channels !== channels) {
    throw new Error("Certificate image could not be converted to RGB");
  }

  const input =
    layout === "NCHW"
      ? toNchw(data, width, height)
      : toNhwc(data);

  const tensor = new ort.Tensor(
    "float32",
    input,
    layout === "NCHW"
      ? [1, 3, height, width]
      : [1, height, width, 3],
  );

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
  const threshold = FALLBACK_THRESHOLD;
  const classification =
    tamperProbability >= threshold ? "TAMPERED" : "GENUINE";
  const confidence =
    classification === "TAMPERED"
      ? tamperProbability
      : 1 - tamperProbability;

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
