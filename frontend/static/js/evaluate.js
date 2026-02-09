// Evaluation page JavaScript

let currentReportType = null;
let currentRubrics = [];
let currentStudentId = null;
let currentEvaluationId = null;

// Load report types on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM loaded, initializing evaluate page...');
    
    // Load report types immediately
    try {
        await loadReportTypes();
        // Small delay to ensure DOM is ready
        setTimeout(async () => {
            await handleReportCategoryChange();
        }, 100);
    } catch (error) {
        console.error('Error loading report types:', error);
        // Try to populate anyway
        setTimeout(async () => {
            await handleReportCategoryChange();
        }, 500);
    }
    
    // Setup report category change listener
    const reportCategory = document.getElementById('reportCategory');
    if (reportCategory) {
        reportCategory.addEventListener('change', handleReportCategoryChange);
        // Also trigger once on load to populate dropdown
        setTimeout(() => {
            handleReportCategoryChange();
        }, 200);
    } else {
        // If category select not found, still try to populate report types
        setTimeout(() => {
            handleReportCategoryChange();
        }, 300);
    }
    
    // Load report types info (non-blocking)
    loadReportTypesInfo().catch(err => console.error('Error loading report types info:', err));
    
    // Setup event listeners
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.addEventListener('click', handleContinue);
    } else {
        console.error('Continue button not found!');
    }
    
    const submitBtn = document.getElementById('submitEvaluation');
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmitEvaluation);
    }
    
    const evaluationMethod = document.getElementById('evaluationMethod');
    if (evaluationMethod) {
        evaluationMethod.addEventListener('change', handleEvaluationMethodChange);
    }
    
    const downloadHTML = document.getElementById('downloadHTML');
    const downloadPDF = document.getElementById('downloadPDF');
    const newEvaluation = document.getElementById('newEvaluation');
    
    if (downloadHTML) downloadHTML.addEventListener('click', () => downloadReport('html'));
    if (downloadPDF) downloadPDF.addEventListener('click', () => downloadReport('pdf'));
    if (newEvaluation) newEvaluation.addEventListener('click', () => location.reload());
    
    // Also try loading after a short delay as fallback
    setTimeout(async () => {
        const select = document.getElementById('reportType');
        if (select && select.options.length === 1) {
            console.log('Report types not loaded, retrying...');
            await loadReportTypes();
        }
    }, 1000);
});

// Map report categories to report types
// This mapping is kept for reference but not used for filtering
// All report types are always shown regardless of category selection
const categoryToReportTypes = {
    'bachelor': ['Research-Driven Thesis', 'Design-Driven Thesis', 'Design-Driven and Small Evaluation Thesis'],
    'master': ['Research-Driven Thesis', 'Design-Driven Thesis', 'Design-Driven and Small Evaluation Thesis', 'Machine Learning or NLP-Based Theses'],
    'seminar': ['Seminar Report'],
    'research': ['Research-Driven Thesis', 'Machine Learning or NLP-Based Theses']
};

// Map display names to database names
const displayNameToDbName = {
    'Research-Driven Thesis': 'Research-Driven Thesis',
    'Design-Driven and Small Evaluation Thesis': 'Design-Driven and Small Evaluation Thesis',
    'Design-Driven Thesis': 'Design-Driven Thesis',
    'Machine Learning or NLP-Based Theses': 'Machine Learning or NLP-Based Theses',
    'Seminar Report': 'Seminar Report'
};

async function handleReportCategoryChange() {
    const category = document.getElementById('reportCategory')?.value || '';
    const reportTypeSelect = document.getElementById('reportType');
    
    if (!reportTypeSelect) {
        console.error('Report type select not found');
        return;
    }
    
    // Use cached report types if available
    let allReportTypes = window.allReportTypes;
    
    if (!allReportTypes || allReportTypes.length === 0) {
        try {
            console.log('Loading report types...');
            allReportTypes = await apiCall('/report-types');
            window.allReportTypes = allReportTypes;
            console.log('Report types loaded:', allReportTypes);
        } catch (error) {
            console.error('Error loading report types:', error);
            showError('Failed to load report types: ' + (error.message || 'Unknown error'));
            return;
        }
    }
    
    // Clear existing options except the first one (placeholder)
    while (reportTypeSelect.options.length > 1) {
        reportTypeSelect.remove(1);
    }
    
    // Define display order (as shown in the image)
    const displayOrder = [
        'Machine Learning or NLP-Based Theses',
        'Research-Driven Thesis',
        'Design-Driven and Small Evaluation Thesis',
        'Design-Driven Thesis',
        'Seminar Report'
    ];
    
    // ALWAYS show ALL types regardless of category selection
    // This matches the requirement: all types should be visible even when "Seminar Report" is selected
    let typesToShow = [];
    if (Array.isArray(allReportTypes)) {
        allReportTypes.forEach(type => {
            typesToShow.push({ id: type.id, name: type.name });
        });
    }
    
    console.log('Category selected:', category);
    console.log('Showing ALL types (no filtering):', typesToShow.map(t => t.name));
    
    // Add options in the specified order
    displayOrder.forEach(displayName => {
        const type = typesToShow.find(t => t.name === displayName);
        if (type) {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = displayName;
            reportTypeSelect.appendChild(option);
            console.log('Added option:', displayName, 'with ID:', type.id);
        } else {
            console.warn('Report type not found in database:', displayName);
        }
    });
    
    // Add any remaining types not in displayOrder
    typesToShow.forEach(type => {
        if (!displayOrder.includes(type.name)) {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            reportTypeSelect.appendChild(option);
            console.log('Added additional option:', type.name);
        }
    });
    
    // Enable the dropdown
    reportTypeSelect.disabled = false;
    console.log(`Loaded ${reportTypeSelect.options.length - 1} report types into dropdown`);
    
    // Trigger validation
    if (typeof checkFormValidity === 'function') {
        checkFormValidity();
    }
}

async function loadReportTypes() {
    try {
        console.log('Loading report types...');
        const reportTypes = await apiCall('/report-types');
        console.log('Report types received:', reportTypes);
        
        // Store report types globally for filtering
        window.allReportTypes = reportTypes;
        
        const select = document.getElementById('reportType');
        if (!select) {
            console.error('Report type select element not found!');
            return;
        }
        
        // Initially disable - will be populated by handleReportCategoryChange
        select.disabled = false;
        
        // Add styling event listener
        select.addEventListener('change', function() {
            if (this.value) {
                this.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05))';
                this.style.borderColor = 'var(--primary-color)';
                this.style.fontWeight = '600';
            } else {
                this.style.background = 'var(--bg-primary)';
                this.style.borderColor = 'var(--border-color)';
                this.style.fontWeight = '500';
            }
        });
        
        // Also add styling to report category dropdown
        const categorySelect = document.getElementById('reportCategory');
        if (categorySelect) {
            categorySelect.addEventListener('change', function() {
                if (this.value) {
                    this.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05))';
                    this.style.borderColor = 'var(--primary-color)';
                    this.style.fontWeight = '600';
                } else {
                    this.style.background = 'var(--bg-primary)';
                    this.style.borderColor = 'var(--border-color)';
                    this.style.fontWeight = '500';
                }
            });
        }
        
    } catch (error) {
        console.error('Error loading report types:', error);
        showError('Failed to load report types: ' + (error.message || 'Unknown error'));
    }
}

async function loadReportTypesInfo() {
    try {
        const reportTypes = await apiCall('/report-types');
        const infoDiv = document.getElementById('reportTypesList');
        const infoBox = document.getElementById('reportTypesInfo');
        
        if (!infoDiv || !infoBox) return;
        
        for (const type of reportTypes) {
            const rubrics = await apiCall(`/report-types/${type.id}/rubrics`);
            const typeDiv = document.createElement('div');
            typeDiv.className = 'info-box';
            typeDiv.style.marginTop = '1rem';
            
            let rubricsHTML = '<ul>';
            rubrics.forEach(rubric => {
                rubricsHTML += `<li>${rubric.section_name} (${rubric.max_points} points)</li>`;
            });
            rubricsHTML += '</ul>';
            
            typeDiv.innerHTML = `
                <h4>${type.name}</h4>
                ${rubricsHTML}
            `;
            infoDiv.appendChild(typeDiv);
        }
        
        infoBox.style.display = 'block';
    } catch (error) {
        console.error('Failed to load report types info:', error);
    }
}

async function handleContinue() {
    console.log('Continue button clicked');
    
    // Check if button is disabled
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn && continueBtn.disabled) {
        showError('Please fill in all required fields');
        return;
    }
    
    if (!checkFormValidity()) {
        showError('Please fill in all required fields');
        return;
    }
    
    const form = document.getElementById('evaluationForm');
    if (!form) {
        showError('Form not found');
        return;
    }
    
    const formData = new FormData(form);
    
    // Validate required fields
    const firstName = formData.get('firstName');
    const lastName = formData.get('lastName');
    const matriculationNumber = formData.get('matriculationNumber');
    const reportCategory = formData.get('reportCategory');
    const reportType = formData.get('reportType');
    const reportTitle = formData.get('reportTitle');
    
    if (!firstName || !lastName || !matriculationNumber || !reportCategory || !reportType || !reportTitle) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Validate matriculation number length
    if (matriculationNumber.length !== 7) {
        showError('Matriculation number must be exactly 7 digits');
        return;
    }
    
    if (!/^\d{7}$/.test(matriculationNumber)) {
        showError('Matriculation number must contain only digits');
        return;
    }
    
    // Disable button during processing
    if (continueBtn) {
        continueBtn.disabled = true;
        continueBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }
    
    // Create or get student, then redirect to step 2
    try {
        console.log('Creating student...');
        const student = await apiCall('/students/', {
            method: 'POST',
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                matriculation_number: matriculationNumber
            })
        });
        
        console.log('Student created:', student);
        const reportTypeSelect = document.getElementById('reportType');
        const reportTypeName = reportTypeSelect && reportTypeSelect.options[reportTypeSelect.selectedIndex]
            ? reportTypeSelect.options[reportTypeSelect.selectedIndex].text
            : '';
        
        const step2Data = {
            studentId: student.id,
            reportTypeId: parseInt(reportType),
            reportTitle: formData.get('reportTitle'),
            oberseminarDate: formData.get('oberseminarDate') || null,
            oberseminarTime: formData.get('oberseminarTime') || null,
            studentFirstName: firstName,
            studentLastName: lastName,
            reportTypeName: reportTypeName
        };
        sessionStorage.setItem('evaluationStep2Data', JSON.stringify(step2Data));
        window.location.href = '/evaluate-step2';
        return;
        
    } catch (error) {
        console.error('Error in handleContinue:', error);
        showError('Failed to create student: ' + (error.message || 'Unknown error'));
        
        // Re-enable button on error
        if (continueBtn) {
            continueBtn.disabled = false;
            continueBtn.innerHTML = 'Continue';
        }
    }
}

async function loadRubrics(reportTypeId) {
    try {
        currentRubrics = await apiCall(`/report-types/${reportTypeId}/rubrics`);
        const container = document.getElementById('rubricsContainer');
        if (!container) return;
        container.innerHTML = '';
        
        currentRubrics.forEach((rubric, index) => {
            const rubricDiv = document.createElement('div');
            rubricDiv.className = 'rubric-item';
            rubricDiv.innerHTML = `
                <h4><i class="fas fa-check-circle" style="color: var(--primary-color);"></i> ${rubric.section_name}</h4>
                <p class="max-points"><i class="fas fa-star"></i> Max Points: ${rubric.max_points}</p>
                ${rubric.description ? `<p style="color: var(--text-secondary); margin: 0.75rem 0;">${rubric.description}</p>` : ''}
                <label><i class="fas fa-pencil-alt"></i> Score:</label>
                <input type="number" 
                       class="score-input" 
                       data-rubric-id="${rubric.id}" 
                       min="0" 
                       max="${rubric.max_points}" 
                       step="0.1" 
                       value="0"
                       required>
                <label><i class="fas fa-comment"></i> Feedback (optional):</label>
                <textarea class="feedback-input" 
                          data-rubric-id="${rubric.id}" 
                          placeholder="Enter feedback for this section..."></textarea>
            `;
            container.appendChild(rubricDiv);
        });
    } catch (error) {
        showError('Failed to load rubrics: ' + error.message);
    }
}

function handleEvaluationMethodChange() {
    const method = document.getElementById('evaluationMethod').value;
    const reportContentSection = document.getElementById('reportContentSection');
    const rubricsContainer = document.getElementById('rubricsContainer');
    
    if (method === 'manual') {
        reportContentSection.style.display = 'none';
        rubricsContainer.style.display = 'block';
    } else {
        reportContentSection.style.display = 'block';
        if (method === 'llm' || method === 'rule-based') {
            rubricsContainer.style.display = 'none';
        } else {
            rubricsContainer.style.display = 'block';
        }
    }
}

async function handleSubmitEvaluation() {
    const method = document.getElementById('evaluationMethod').value;
    const form = document.getElementById('evaluationForm');
    const formData = new FormData(form);
    
    try {
        let evaluation;
        
        if (method === 'manual') {
            // Manual evaluation
            const scores = [];
            currentRubrics.forEach(rubric => {
                const scoreInput = document.querySelector(`.score-input[data-rubric-id="${rubric.id}"]`);
                const feedbackInput = document.querySelector(`.feedback-input[data-rubric-id="${rubric.id}"]`);
                
                if (scoreInput) {
                    scores.push({
                        rubric_id: rubric.id,
                        score: parseFloat(scoreInput.value) || 0,
                        feedback: feedbackInput ? feedbackInput.value : null
                    });
                }
            });
            
            evaluation = await apiCall('/evaluations/', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: currentStudentId,
                    report_type_id: currentReportType,
                    report_title: formData.get('reportTitle'),
                    oberseminar_date: formData.get('oberseminarDate'),
                    oberseminar_time: formData.get('oberseminarTime'),
                    evaluation_method: 'manual',
                    scores: scores
                })
            });
            
        } else if (method === 'llm') {
            const reportContent = document.getElementById('reportContent').value;
            if (!reportContent.trim()) {
                showError('Please provide report content for language model evaluation');
                return;
            }
            
            evaluation = await apiCall('/evaluations/llm', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: currentStudentId,
                    report_type_id: currentReportType,
                    report_title: formData.get('reportTitle'),
                    report_content: reportContent
                })
            });
            
        } else if (method === 'rule-based') {
            // Rule-based evaluation
            const reportContent = document.getElementById('reportContent').value;
            if (!reportContent.trim()) {
                showError('Please provide report content for rule-based evaluation');
                return;
            }
            
            evaluation = await apiCall('/evaluations/rule-based', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: currentStudentId,
                    report_type_id: currentReportType,
                    report_title: formData.get('reportTitle'),
                    report_content: reportContent
                })
            });
        }
        
        currentEvaluationId = evaluation.id;
        showResults(evaluation);
        
    } catch (error) {
        showError('Failed to submit evaluation: ' + error.message);
    }
}

function showResults(evaluation) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    
    const percentage = evaluation.max_possible_score > 0 
        ? (evaluation.total_score / evaluation.max_possible_score * 100).toFixed(2)
        : 0;
    
    let scoresHTML = '<table><thead><tr><th>Section</th><th>Score</th><th>Max Points</th><th>Feedback</th></tr></thead><tbody>';
    
    evaluation.rubrics.forEach(rubric => {
        scoresHTML += `
            <tr>
                <td><strong>${rubric.section_name}</strong></td>
                <td>${rubric.score || 0}</td>
                <td>${rubric.max_points}</td>
                <td>${rubric.feedback || 'No feedback'}</td>
            </tr>
        `;
    });
    
    scoresHTML += '</tbody></table>';
    
    resultsContent.innerHTML = `
        <div class="results-summary">
            <h3><i class="fas fa-chart-line"></i> Evaluation Summary</h3>
            <p><i class="fas fa-user-graduate"></i> <strong>Student:</strong> ${evaluation.student.first_name} ${evaluation.student.last_name}</p>
            <p><i class="fas fa-file-alt"></i> <strong>Report Title:</strong> ${evaluation.report_title}</p>
            <p class="total-score"><i class="fas fa-trophy"></i> Total Score: ${evaluation.total_score} / ${evaluation.max_possible_score} (${percentage}%)</p>
            <p><i class="fas fa-cogs"></i> <strong>Evaluation Method:</strong> ${evaluation.evaluation_method}</p>
        </div>
        <h3><i class="fas fa-list-ol"></i> Detailed Scores</h3>
        ${scoresHTML}
    `;
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function downloadReport(format) {
    if (!currentEvaluationId) {
        showError('No evaluation available to download');
        return;
    }
    
    const url = `/api/evaluations/${currentEvaluationId}/report/${format}`;
    window.open(url, '_blank');
}

