/**
 * Input sanitization and validation following @systematic-debugging best practices.
 */
export function validateGenerateRequest(body) {
  if (!body || typeof body !== "object") {
    return { valid: false, error: "Invalid request payload: must be a valid JSON object." };
  }

  const { topic, track, customDescription, provider, apiKey } = body;

  if (!topic && !customDescription) {
    return { valid: false, error: "Missing required parameter: either 'topic' or 'customDescription' must be provided." };
  }

  // Sanitize strings
  const sanitizedTopic = typeof topic === "string" ? topic.trim().slice(0, 200) : "";
  const sanitizedTrack = typeof track === "string" ? track.trim().slice(0, 100) : "";
  const sanitizedDesc = typeof customDescription === "string" ? customDescription.trim().slice(0, 1000) : "";

  return {
    valid: true,
    data: {
      topic: sanitizedTopic,
      track: sanitizedTrack,
      customDescription: sanitizedDesc,
      provider: provider === "gemini" || provider === "openai" ? provider : "built-in",
      apiKey: typeof apiKey === "string" ? apiKey.trim() : ""
    }
  };
}

export function validateSimulationRequest(body) {
  if (!body || typeof body !== "object") {
    return { valid: false, error: "Request body must be an object." };
  }
  const { input, topic } = body;
  if (!input || typeof input !== "string" || input.trim().length === 0) {
    return { valid: false, error: "Input payload is required for simulation." };
  }
  return {
    valid: true,
    data: {
      input: input.trim().slice(0, 2000),
      topic: typeof topic === "string" ? topic.trim() : "generic"
    }
  };
}
