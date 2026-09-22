import fs from "node:fs";
import path from "node:path";
import * as ort from "onnxruntime-node";
import sharp from "sharp";

let sessionPromise: Promise<ort.InferenceSession> | undefined;

function modelPath() {
  return path.join(process.cwd(), "models", "certificate_tamper_model.onnx");
}

async function getSession() {
  if (!fs.existsSync(modelPath())) {
    throw new Error("AI model file is not deployed");
  }
  sessionPromise ??= ort.InferenceSession.create(modelPath());
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

  const input = new Float32Array(224 * 224 * 3);
  for (let i = 0; i < data.length; i++) {
    input[i] = data[i];
  }

  const session = await getSession();
  const inputName = session.inputNames[0];
  const outputName = session.outputNames[0];
  const tensor = new ort.Tensor("float32", input, [1, 224, 224, 3]);
  const result = await session.run({ [inputName]: tensor });
  const output = result[outputName] as ort.Tensor;
  const probability = Number(output.data[0]);

  if (!Number.isFinite(probability)) {
    throw new Error("AI model returned an invalid prediction");
  }

  const tamperProbability = Math.max(0, Math.min(1, probability));
  const classification = tamperProbability >= 0.5 ? "TAMPERED" : "GENUINE";
  const confidence = classification === "TAMPERED"
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
