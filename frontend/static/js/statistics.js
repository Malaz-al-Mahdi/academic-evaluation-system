// Statistics page JavaScript

document.addEventListener('DOMContentLoaded', async () => {
    await loadStatistics();
});

async function loadStatistics() {
    try {
        const statistics = await apiCall('/report-types/statistics/all');
        const container = document.getElementById('statisticsContainer');
        container.innerHTML = '';

        if (statistics.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No statistics available yet.</p>';
            return;
        }

        statistics.forEach(stat => {
            const statCard = document.createElement('div');
            statCard.className = 'info-box';
            statCard.style.padding = '1.5rem';
            
            const percentage = stat.average_percentage || 0;
            const percentageColor = percentage >= 80 ? '#10b981' : percentage >= 60 ? '#f59e0b' : '#ef4444';
            
            statCard.innerHTML = `
                <h3 style="margin-bottom: 1rem; color: var(--primary-color);">
                    <i class="fas fa-file-alt"></i> ${stat.report_type_name}
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Total Evaluations</div>
                        <div style="font-size: 1.5rem; font-weight: 600;">${stat.total_evaluations}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Average Score</div>
                        <div style="font-size: 1.5rem; font-weight: 600;">${stat.average_score.toFixed(2)} / ${stat.max_possible_score.toFixed(2)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Average Percentage</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: ${percentageColor};">${percentage.toFixed(1)}%</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Min Score</div>
                        <div style="font-weight: 600;">${stat.min_score.toFixed(2)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Max Score</div>
                        <div style="font-weight: 600;">${stat.max_score.toFixed(2)}</div>
                    </div>
                </div>
            `;
            
            container.appendChild(statCard);
        });
    } catch (error) {
        console.error('Error loading statistics:', error);
        showError('Failed to load statistics: ' + (error.message || 'Unknown error'));
    }
}
