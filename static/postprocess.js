// Helper function: Find the best consecutive keys
function findBestConsecutiveKeys(data, distance = 4) {
    // Convert data (object) to an array of key-value pairs and sort by value
    const sortedItems = Object.entries(data).sort((a, b) => a[1] - b[1]);
    let result = [];
    let currentSequence = [parseInt(sortedItems[0][0])]; // Start with the key of the first item

    for (let i = 1; i < sortedItems.length; i++) {
        const currentKey = parseInt(sortedItems[i][0]);
        const currentValue = sortedItems[i][1];
        const prevValue = sortedItems[i - 1][1];

        // Check if the values are consecutive or allow for one gap
        if (currentValue === prevValue + 1 || currentValue === prevValue + 2) {
            currentSequence.push(currentKey);
        } else {
            // If the sequence is broken, save it and start a new one
            if (currentSequence.length > 1) {
                result.push(currentSequence);
            }
            currentSequence = [currentKey];
        }
    }

    // Add the last sequence
    if (currentSequence.length > 1) {
        result.push(currentSequence);
    }

    // Eliminate sequences where distances between consecutive keys are less than 'distance'
    const filteredResult = result.filter(sequence =>
        sequence.every((key, index) =>
            index === 0 || Math.abs(key - sequence[index - 1]) >= distance
        )
    );

    // Select the sequence with the largest sum of values
    const bestSequence = filteredResult.reduce((best, sequence) => {
        const sumValues = sequence.reduce((sum, key) => sum + data[key], 0);
        const bestSum = best.reduce((sum, key) => sum + data[key], 0);
        return sumValues > bestSum ? sequence : best;
    }, []);

    return bestSequence;
}

function insert_breaks(doc) {

    const possibleIndexes = {};
    const lines = doc.querySelectorAll(lc); // Adjust for JS DOM

    lines.forEach((line, i) => {
        const words = line.querySelectorAll(".ocrx_word");
        if (words.length === 1) {
            const word = words[0].textContent.trim();
            if (word.match(/^[0-9]+$/) != null) {
                possibleIndexes[i] = parseInt(word, 10); // Save index and numeric value
            }
        }
    });

    const bestIndexes = findBestConsecutiveKeys(possibleIndexes);
    console.log(bestIndexes);

    const filteredLines = Array.from(lines).filter((_, i) => bestIndexes.includes(i));

    filteredLines.forEach(line => {
        // Step 1: Check if the line has previous and next siblings
        const prevSiblings = [];
        let prev = line.previousElementSibling; // Only consider element siblings
        while (prev && prev.classList.contains("ocrx_line")) {
            prevSiblings.unshift(prev); // Collect previous siblings
            prev = prev.previousElementSibling;
        }

        const nextSiblings = [];
        let next = line.nextElementSibling; // Only consider element siblings
        while (next && next.classList.contains("ocrx_line")) {
            nextSiblings.push(next); // Collect next siblings
            next = next.nextElementSibling;
        }

        // Get the parent ".ocrx_par" element
        const parentPar = line.closest(".ocr_par");
        if (!parentPar) {
            console.warn("No parent with class '.ocr_par' found for", line);
            return;
        }

        // Step 2: Split the parent ".ocrx_par" into groups
        const parentAttributes = Array.from(parentPar.attributes); // Copy original attributes

        // Create new parent for previous siblings (if exist)
        if (prevSiblings.length > 0) {
            const newPrevPar = document.createElement("div");
            newPrevPar.classList.add("ocr_par");
            parentAttributes.forEach((attr) => newPrevPar.setAttribute(attr.name, attr.value));
            prevSiblings.forEach((sibling) => newPrevPar.appendChild(sibling));
            parentPar.parentNode.insertBefore(newPrevPar, parentPar);
        }

        // Create new parent for next siblings (if exist)
        if (nextSiblings.length > 0) {
            const newNextPar = document.createElement("div");
            newNextPar.classList.add("ocr_par");
            parentAttributes.forEach((attr) => newNextPar.setAttribute(attr.name, attr.value));
            nextSiblings.forEach((sibling) => newNextPar.appendChild(sibling));
            parentPar.parentNode.insertBefore(newNextPar, parentPar.nextSibling);
        }

        // Step 3: In the par that contains the line of interest, append the "break" element before the line
        const breakElement = document.createElement("div");
        breakElement.classList.add("break");
        breakElement.innerHTML = "BREAK"
        parentPar.parentNode.insertBefore(breakElement, parentPar);
    });

    alert("ХТМЛ је у потпуности обрађен и распарчан на акта.");
}



