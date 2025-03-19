function postprocess(htmlString) {
    // Parse the HTML string into a DOM Document
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, "text/html");

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

    const possibleIndexes = {};
    const lines = doc.querySelectorAll("p"); // Adjust for JS DOM

    lines.forEach((line, i) => {
        words = line.textContent.trim().split(/\s+/);
        if (words.length === 1) {
            const word = words[0]
            if (word.match(/^[0-9]+$/) != null) {
                possibleIndexes[i] = parseInt(word, 10); // Save index and numeric value
            }
        }
    });

    const bestIndexes = findBestConsecutiveKeys(possibleIndexes);
    console.log(bestIndexes);

    const filteredLines = Array.from(lines).filter((_, i) => bestIndexes.includes(i));

    filteredLines.forEach(line => {
        line.className = "broj";
    });

    // Find all "p.broj" elements in the document
     // Find all "p.broj" elements in the document
     const brojElements = Array.from(doc.querySelectorAll("p.broj"));

     // If no "p.broj" elements are found, return an empty array
     if (brojElements.length === 0) {
         return [];
     }
 
     // Array to hold the split documents
     const splitDocs = [];
 
     // Iterate through each "p.broj" element
     brojElements.forEach((broj, index) => {
         // Create a new document for this segment
         const newDoc = document.implementation.createHTMLDocument("Split Doc");
 
         // Add this "p.broj" element to the new document
         newDoc.body.appendChild(broj.cloneNode(true));
 
         // Add the content after this "p.broj" but stop at the next "p.broj"
         let currentNode = broj.nextSibling;
         while (currentNode && !currentNode.matches?.("p.broj")) {
             const nextNode = currentNode.nextSibling; // Save reference to the next node
             newDoc.body.appendChild(currentNode.cloneNode(true)); // Clone and append to the new document
             currentNode = nextNode;
         }
 
         // Convert the new document back to an HTML string and store it
         splitDocs.push(newDoc.documentElement.outerHTML);
     });
 
     // Return the array of split documents as HTML strings
     return splitDocs;
}
