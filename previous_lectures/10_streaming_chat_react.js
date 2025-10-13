"use client";
import React, { useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

export default function Stream() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { type: "user", content: input };
    const currentInput = input;
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    let aiResponse = "";
    const aiMessage = { type: "ai", content: "Thinking..." };
    setMessages((prev) => [...prev, aiMessage]);

    const abortController = new AbortController();

    try {
      await fetchEventSource("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_input: currentInput }),
        signal: abortController.signal,
        onmessage: (event) => {
          if (event.data === "[DONE]") {
            abortController.abort();
            setIsLoading(false);
            return;
          }

          try {
            const data = JSON.parse(event.data);
            // Changed from data.message to data.answer
            if (data.answer) {
              aiResponse += data.answer;

              setMessages((prev) =>
                prev.map((msg, index) =>
                  index === prev.length - 1
                    ? { ...msg, content: aiResponse }
                    : msg
                )
              );
            }
          } catch (parseError) {
            console.error("Parse error:", parseError);
          }
        },
        onclose: () => {
          setIsLoading(false);
        },
        onerror: (err) => {
          console.error("Stream error:", err);
          setIsLoading(false);
          abortController.abort();
          throw err;
        },
        onopen: async (response) => {
          if (response.ok) {
            return;
          } else {
            throw new Error(`${response.status}: ${response.statusText}`);
          }
        },
      });
    } catch (error) {
      console.error("Error:", error);
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div
        style={{
          height: "400px",
          overflowY: "scroll",
          border: "1px solid #ccc",
          padding: "10px",
          marginBottom: "10px",
        }}
      >
        {messages.map((message, index) => (
          <div key={index} style={{ marginBottom: "10px" }}>
            <strong>{message.type === "user" ? "You: " : "AI: "}</strong>
            {message.content}
          </div>
        ))}
        {isLoading && <div>AI is typing...</div>}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{ width: "300px", padding: "5px" }}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
