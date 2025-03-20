// Helper function: Find the best consecutive keys
function findBestConsecutiveKeys(data, distance = 4, allowGap = true) {
    const keys = Object.keys(data).map(Number); // Extract keys as numbers
    const values = Object.values(data); // Extract values
    let result = [];

    // Iterate through the values
    values.forEach((value, index) => {
        let currentSequence = [{ key: keys[index], value }]; // Start a new sequence with the current item

        for (let i = 0; i < values.length; i++) {
            if (i === index) continue; // Skip the current value itself

            const nextKey = keys[i];
            const nextValue = values[i];
            const keyDifference = nextKey - currentSequence[currentSequence.length - 1].key;
            const valueDifference = nextValue - currentSequence[currentSequence.length - 1].value;

            // Check if conditions for consecutiveness (and key distance) are met
            if (
                keyDifference >= distance &&
                (valueDifference === 1 || (allowGap && valueDifference === 2))
            ) {
                currentSequence.push({ key: nextKey, value: nextValue });
            }
        }
        // Add the found sequence to the result
        if (currentSequence.length > 1) {
            result.push(currentSequence);
        }
    });

    // Find the longest sequence
    let longestSequence = result.reduce((longest, current) => 
        current.length > longest.length ? current : longest, []);

    // Extract and return the keys of the longest sequence
    const longestKeys = longestSequence.map(item => item.key);
    return longestKeys;
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
    const filteredLines = Array.from(lines).filter((_, i) => bestIndexes.includes(i));

    filteredLines.forEach(line => {
        // Step 1: Check if the line has previous and next siblings
        const prevSiblings = [];
        let prev = line.previousElementSibling; // Only consider element siblings
        while (prev && prev.classList.contains(lc)) {
            prevSiblings.unshift(prev); // Collect previous siblings
            prev = prev.previousElementSibling;
        }

        const nextSiblings = [];
        let next = line.nextElementSibling; // Only consider element siblings
        while (next && next.classList.contains(lc)) {
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

    alert("Документ је у потпуности обрађен и распарчан на акта.");
}



