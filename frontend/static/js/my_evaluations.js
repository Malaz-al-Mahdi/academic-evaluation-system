// My Evaluations page JavaScript

document.addEventListener('DOMContentLoaded', async () => {
    await loadMyEvaluations();
});

async function loadMyEvaluations() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const evaluationsContainer = document.getElementById('evaluationsContainer');
    const evaluationsList = document.getElementById('evaluationsList');
    const noResults = document.getElementById('noResults');

    try {
        const evaluations = await apiCall('/evaluations/my');
        
        loadingIndicator.style.display = 'none';
        
        if (!evaluations || evaluations.length === 0) {
            noResults.style.display = 'block';
            return;
        }

        evaluationsContainer.style.display = 'block';
        evaluationsList.innerHTML = '';

        evaluations.forEach(evaluation => {
            const percentage = evaluation.max_possible_score > 0
                ? ((evaluation.total_score / evaluation.max_possible_score) * 100).toFixed(1)
                : 0;
            const percentageColor = percentage >= 80 ? '#10b981' : percentage >= 60 ? '#f59e0b' : '#ef4444';
            const date = evaluation.created_at ? new Date(evaluation.created_at).toLocaleDateString('de-DE', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : 'Unknown date';

            const card = document.createElement('div');
            card.className = 'info-box';
            card.style.marginBottom = '1rem';
            card.style.padding = '1.5rem';
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                    <div style="flex: 1; min-width: 200px;">
                        <h3 style="margin: 0 0 0.5rem 0; color: var(--primary-color);">
                            <i class="fas fa-file-alt"></i> ${evaluation.report_title || 'Untitled Report'}
                        </h3>
                        <p style="margin: 0.25rem 0; color: var(--text-secondary);">
                            <i class="fas fa-user-graduate"></i> 
                            <strong>${evaluation.student?.first_name || ''} ${evaluation.student?.last_name || ''}</strong>
                            ${evaluation.student?.matriculation_number ? `(${evaluation.student.matriculation_number})` : ''}
                        </p>
                        <p style="margin: 0.25rem 0; color: var(--text-secondary);">
                            <i class="fas fa-folder"></i> ${evaluation.report_type?.name || 'Unknown Type'}
                        </p>
                        <p style="margin: 0.25rem 0; color: var(--text-secondary);">
                            <i class="fas fa-calendar"></i> ${date}
                        </p>
                        <p style="margin: 0.25rem 0; color: var(--text-secondary);">
                            <i class="fas fa-cogs"></i> Method: ${evaluation.evaluation_method || 'manual'}
                        </p>
                    </div>
                    <div style="text-align: right; min-width: 150px;">
                        <div style="font-size: 2rem; font-weight: 700; color: ${percentageColor};">
                            ${percentage}%
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                            ${evaluation.total_score?.toFixed(1) || 0} / ${evaluation.max_possible_score?.toFixed(1) || 0} points
                        </div>
                        <div style="margin-top: 1rem;">
                            <button class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.875rem;" onclick="downloadReport(${evaluation.id}, 'html')">
                                <i class="fas fa-file-code"></i> HTML
                            </button>
                            <button class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.875rem; margin-left: 0.5rem;" onclick="downloadReport(${evaluation.id}, 'pdf')">
                                <i class="fas fa-file-pdf"></i> PDF
                            </button>
                        </div>
                    </div>
                </div>
            `;
            evaluationsList.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading evaluations:', error);
        loadingIndicator.style.display = 'none';
        noResults.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem; color: #ef4444;"></i>
            <p>Failed to load evaluations: ${error.message || 'Unknown error'}</p>
        `;
        noResults.style.display = 'block';
    }
}

function downloadReport(evaluationId, format) {
    window.open(`/api/evaluations/${evaluationId}/report/${format}`, '_blank');
}
