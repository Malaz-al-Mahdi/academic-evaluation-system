// Step 2: Evaluation rubrics and submit (data comes from sessionStorage set on /evaluate)

let step2Data = null;
let currentRubrics = [];
let currentEvaluationId = null;

document.addEventListener('DOMContentLoaded', async () => {
    const raw = sessionStorage.getItem('evaluationStep2Data');
    if (!raw) {
        window.location.href = '/evaluate';
        return;
    }
    try {
        step2Data = JSON.parse(raw);
    } catch (e) {
        sessionStorage.removeItem('evaluationStep2Data');
        window.location.href = '/evaluate';
        return;
    }

    const infoEl = document.getElementById('step2StudentReport');
    if (infoEl) {
        infoEl.textContent = `${step2Data.studentFirstName} ${step2Data.studentLastName} – ${step2Data.reportTypeName || 'Report'}: ${step2Data.reportTitle || '(no title)'}`;
    }

    try {
        await loadRubrics(step2Data.reportTypeId);
    } catch (err) {
        showError('Failed to load rubrics: ' + (err.message || 'Unknown error'));
    }

    const evaluationMethod = document.getElementById('evaluationMethod');
    if (evaluationMethod) {
        evaluationMethod.addEventListener('change', handleEvaluationMethodChange);
    }

    const submitBtn = document.getElementById('submitEvaluation');
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmitEvaluation);
    }

    const downloadHTML = document.getElementById('downloadHTML');
    const downloadPDF = document.getElementById('downloadPDF');
    const newEvaluation = document.getElementById('newEvaluation');
    if (downloadHTML) downloadHTML.addEventListener('click', () => downloadReport('html'));
    if (downloadPDF) downloadPDF.addEventListener('click', () => downloadReport('pdf'));
    if (newEvaluation) {
        newEvaluation.addEventListener('click', () => {
            sessionStorage.removeItem('evaluationStep2Data');
            window.location.href = '/evaluate';
        });
    }
});

async function loadRubrics(reportTypeId) {
    currentRubrics = await apiCall(`/report-types/${reportTypeId}/rubrics`);
    const container = document.getElementById('rubricsContainer');
    if (!container) return;
    container.innerHTML = '';
    currentRubrics.forEach((rubric) => {
        const rubricDiv = document.createElement('div');
        rubricDiv.className = 'rubric-item';
        rubricDiv.innerHTML = `
            <h4><i class="fas fa-check-circle" style="color: var(--primary-color);"></i> ${rubric.section_name}</h4>
            <p class="max-points"><i class="fas fa-star"></i> Max Points: ${rubric.max_points}</p>
            ${rubric.description ? `<p style="color: var(--text-secondary); margin: 0.75rem 0;">${rubric.description}</p>` : ''}
            <label><i class="fas fa-pencil-alt"></i> Score:</label>
            <input type="number" class="score-input" data-rubric-id="${rubric.id}" min="0" max="${rubric.max_points}" step="0.1" value="0" required>
            <label><i class="fas fa-comment"></i> Feedback (optional):</label>
            <textarea class="feedback-input" data-rubric-id="${rubric.id}" placeholder="Enter feedback for this section..."></textarea>
        `;
        container.appendChild(rubricDiv);
    });
}

function handleEvaluationMethodChange() {
    const method = document.getElementById('evaluationMethod')?.value || 'manual';
    const reportContentSection = document.getElementById('reportContentSection');
    const rubricsContainer = document.getElementById('rubricsContainer');
    if (reportContentSection) reportContentSection.style.display = (method === 'manual') ? 'none' : 'block';
    if (rubricsContainer) rubricsContainer.style.display = (method === 'llm' || method === 'rule-based') ? 'none' : 'block';
}

async function handleSubmitEvaluation() {
    const method = document.getElementById('evaluationMethod')?.value || 'manual';
    try {
        let evaluation;
        if (method === 'manual') {
            const scores = currentRubrics.map(rubric => {
                const scoreInput = document.querySelector(`.score-input[data-rubric-id="${rubric.id}"]`);
                const feedbackInput = document.querySelector(`.feedback-input[data-rubric-id="${rubric.id}"]`);
                return {
                    rubric_id: rubric.id,
                    score: scoreInput ? (parseFloat(scoreInput.value) || 0) : 0,
                    feedback: feedbackInput ? feedbackInput.value : null
                };
            });
            evaluation = await apiCall('/evaluations/', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: step2Data.studentId,
                    report_type_id: step2Data.reportTypeId,
                    report_title: step2Data.reportTitle,
                    oberseminar_date: step2Data.oberseminarDate,
                    oberseminar_time: step2Data.oberseminarTime,
                    evaluation_method: 'manual',
                    scores: scores
                })
            });
        } else if (method === 'llm') {
            const reportContent = document.getElementById('reportContent')?.value?.trim() || '';
            if (!reportContent) {
                showError('Please provide report content for language model evaluation');
                return;
            }
            evaluation = await apiCall('/evaluations/llm', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: step2Data.studentId,
                    report_type_id: step2Data.reportTypeId,
                    report_title: step2Data.reportTitle,
                    report_content: reportContent
                })
            });
        } else if (method === 'rule-based') {
            const reportContent = document.getElementById('reportContent')?.value?.trim() || '';
            if (!reportContent) {
                showError('Please provide report content for rule-based evaluation');
                return;
            }
            evaluation = await apiCall('/evaluations/rule-based', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: step2Data.studentId,
                    report_type_id: step2Data.reportTypeId,
                    report_title: step2Data.reportTitle,
                    report_content: reportContent
                })
            });
        } else {
            showError('Unknown evaluation method');
            return;
        }
        currentEvaluationId = evaluation.id;
        showResults(evaluation);
    } catch (error) {
        showError('Failed to submit evaluation: ' + (error.message || 'Unknown error'));
    }
}

function showResults(evaluation) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsSection || !resultsContent) return;
    const percentage = evaluation.max_possible_score > 0
        ? (evaluation.total_score / evaluation.max_possible_score * 100).toFixed(2)
        : 0;
    let scoresHTML = '<table><thead><tr><th>Section</th><th>Score</th><th>Max Points</th><th>Feedback</th></tr></thead><tbody>';
    (evaluation.rubrics || []).forEach(rubric => {
        scoresHTML += `<tr><td><strong>${rubric.section_name}</strong></td><td>${rubric.score != null ? rubric.score : 0}</td><td>${rubric.max_points}</td><td>${rubric.feedback || 'No feedback'}</td></tr>`;
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
    window.open(`/api/evaluations/${currentEvaluationId}/report/${format}`, '_blank');
}
