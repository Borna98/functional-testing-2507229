// Sends each form to /api/call and shows the result or the error.
document.querySelectorAll("form.card").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const output = form.querySelector(".result");
    const args = [...form.querySelectorAll("input")].map((input) => input.value);
    output.className = "result loading";
    output.textContent = "Running…";

    try {
      const response = await fetch("/api/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ function: form.dataset.function, args }),
      });
      const data = await response.json();
      output.replaceChildren();

      if (data.call) addLine(output, "call", data.call);
      if (data.ok) {
        output.className = "result ok";
        addLine(output, "value", data.result);
        addLine(output, "meta", "type: " + data.type);
      } else {
        output.className = "result err";
        addLine(output, "value", data.error_type);
        addLine(output, "meta", data.message || "(no message)");
      }
      (data.notes || []).forEach((note) => addLine(output, "note", note));
    } catch (error) {
      output.className = "result err";
      output.textContent = "Network error: " + error.message;
    }
  });
});

function addLine(parent, kind, text) {
  const div = document.createElement("div");
  div.className = kind;
  div.textContent = text;
  parent.appendChild(div);
}

// Category filter chips
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    const filter = chip.dataset.filter;
    document.querySelectorAll("form.card").forEach((card) => {
      card.hidden = filter !== "all" && card.dataset.group !== filter;
    });
  });
});
