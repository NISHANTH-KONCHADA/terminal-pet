document.addEventListener('DOMContentLoaded', () => {
    const terminalOutput = document.getElementById('terminal-output');
    
    const lines = [
        { text: "$ pet status", type: "input", delay: 800 },
        { text: "", type: "output", delay: 300 },
        { text: "     /\\_/\\", type: "output", delay: 100, class: "ascii" },
        { text: "    ( ^.^ )", type: "output", delay: 100, class: "ascii" },
        { text: "     > ^ <", type: "output", delay: 100, class: "ascii" },
        { text: "    /|   |\\", type: "output", delay: 100, class: "ascii" },
        { text: "   (_|   |_)", type: "output", delay: 100, class: "ascii" },
        { text: "", type: "output", delay: 200 },
        { text: "<span style='font-weight:bold;color:#f8fafc'>Pixel</span> the Hatchling", type: "output", delay: 400 },
        { text: "", type: "output", delay: 100 },
        { text: "Hunger:    <span style='color:#22c55e'>[####################] 100%</span>", type: "output", delay: 300 },
        { text: "Happiness: <span style='color:#22c55e'>[####################] 100%</span>", type: "output", delay: 300 },
        { text: "", type: "output", delay: 100 },
        { text: "Total commits:    42", type: "output", delay: 200 },
        { text: "Current streak:   5 day(s)", type: "output", delay: 200 },
        { text: "Longest streak:   12 day(s)", type: "output", delay: 200 },
        { text: "", type: "output", delay: 100 },
        { text: "<span style='color:#0ea5e9'>Your pet is having the BEST day. Keep up that streak!</span>", type: "output", delay: 500 },
        { text: "$ ", type: "input-wait", delay: 500 }
    ];

    let currentLine = 0;

    function typeLine() {
        if (currentLine >= lines.length) return;

        const line = lines[currentLine];
        const lineElem = document.createElement('div');
        
        if (line.class) {
            lineElem.className = line.class;
        }

        if (line.type === "input") {
            lineElem.innerHTML = `<span style="color:#22c55e">➜</span> <span style="color:#0ea5e9">~</span> `;
            terminalOutput.appendChild(lineElem);
            
            let charIndex = 0;
            const textToType = line.text;
            
            function typeChar() {
                if (charIndex < textToType.length) {
                    lineElem.innerHTML += textToType.charAt(charIndex);
                    charIndex++;
                    setTimeout(typeChar, 50);
                } else {
                    currentLine++;
                    setTimeout(typeLine, line.delay);
                }
            }
            typeChar();
        } else if (line.type === "input-wait") {
            lineElem.innerHTML = `<span style="color:#22c55e">➜</span> <span style="color:#0ea5e9">~</span> <span class="cursor"></span>`;
            terminalOutput.appendChild(lineElem);
            currentLine++;
            // Don't call typeLine, just blink cursor
        } else {
            lineElem.innerHTML = line.text || "&nbsp;";
            terminalOutput.appendChild(lineElem);
            currentLine++;
            setTimeout(typeLine, line.delay);
        }
    }

    // Start the animation
    setTimeout(typeLine, 500);
});
