import fs from "node:fs/promises";
import path from "node:path";
import * as ort from "onnxruntime-node";
import sharp from "sharp";

let sessionPromise: Promise<ort.InferenceSession> | undefined;

const MODEL_RELATIVE_PATH = path.join("models", "certificate_tamper_model.onnx");

function modelCandidates() {
  const candidates = [
    path.join(process.cwd(), MODEL_RELATIVE_PATH),
    path.join(process.cwd(), "frontend", MODEL_RELATIVE_PATH),
    path.join(__dirname, MODEL_RELATIVE_PATH),
    path.join(__dirname, "..", "..", MODEL_RELATIVE_PATH),
  ];
  return [...new Set(candidates)];
}

async function getModelBytes() {
  const errors: string[] = [];

  for (const modelPath of modelCandidates()) {
    try {
      const model = await fs.readFile(modelPath);
      if (model.length === 0) throw new Error("empty file");
      return model;
    } catch (error) {
      errors.push(`${modelPath}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  throw new Error(`AI model could not be loaded. Checked: ${errors.join(" | ")}`);
}

async function getSession() {
  if (!sessionPromise) {
    sessionPromise = getModelBytes().then((model) =>
      ort.InferenceSession.create(new Uint8Array(model)),
    );
  }
  return sessionPromise;
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

  const input = Float32Array.from(data, (value) => value);
  const session = await getSession();
  const inputName = session.inputNames[0];
  const outputName = session.outputNames[0];

  if (!inputName || !outputName) {
    throw new Error("AI model has no usable input/output tensors");
  }

  const tensor = new ort.Tensor("float32", input, [1, 224, 224, 3]);
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
