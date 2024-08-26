function updateTerrains(selectElement) {
    const refMessageId = selectElement.value;

    // Fetch terrains based on the selected refMessage
    fetch(`/api/terrains/${refMessageId}/`)
        .then(response => response.json())
        .then(data => {
            const terrainsSelect = document.getElementById('id_choixTerrains');
            terrainsSelect.innerHTML = '';  // Clear existing options

            data.forEach(terrain => {
                const option = document.createElement('option');
                option.value = terrain.id;
                option.textContent = terrain.geo;  // Assuming 'geo' is the name to display
                terrainsSelect.appendChild(option);
            });
        });
}
