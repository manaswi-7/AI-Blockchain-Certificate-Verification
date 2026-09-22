/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ["onnxruntime-node", "sharp"],
  outputFileTracingIncludes: {
    "/api/verify/upload": ["./models/certificate_tamper_model.onnx"],
  },
};

export default nextConfig;
