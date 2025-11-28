// frontend/src/utils/api.js
export async function sendChatMessage(message) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error("Failed to reach backend");
  }

  return res.json();
}
