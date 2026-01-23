// Admin panel JavaScript

document.addEventListener('DOMContentLoaded', async () => {
    await loadReportTypesAdmin();
    
    const uploadBtn = document.getElementById('uploadRubrics');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', handleUploadRubrics);
    }
});

async function loadReportTypesAdmin() {
    try {
        const reportTypes = await apiCall('/report-types');
        const container = document.getElementById('reportTypesAdmin');
        container.innerHTML = '';
        
        for (const type of reportTypes) {
            const rubrics = await apiCall(`/report-types/${type.id}/rubrics`);
            const typeDiv = document.createElement('div');
            typeDiv.className = 'admin-section';
            typeDiv.style.marginTop = '1rem';
            
            let rubricsHTML = '<ul>';
            rubrics.forEach(rubric => {
                rubricsHTML += `<li><strong>${rubric.section_name}</strong> - ${rubric.max_points} points</li>`;
            });
            rubricsHTML += '</ul>';
            
            typeDiv.innerHTML = `
                <h4>${type.name}</h4>
                <p>${type.description || 'No description'}</p>
                <h5>Rubrics:</h5>
                ${rubricsHTML}
            `;
            container.appendChild(typeDiv);
        }
    } catch (error) {
        showError('Failed to load report types: ' + error.message);
    }
}

async function handleUploadRubrics() {
    const fileInput = document.getElementById('rubricFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select a file');
        return;
    }
    
    // File upload requires server-side API endpoint implementation
    showError('File upload functionality requires server-side implementation. Please use the default rubrics or modify them in the database.');
}




