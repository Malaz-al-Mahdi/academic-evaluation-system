// Student history page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('searchBtn');
    const matriculationInput = document.getElementById('matriculationNumber');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
    
    if (matriculationInput) {
        matriculationInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
        
        matriculationInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 7) {
                this.value = this.value.slice(0, 7);
            }
        });
    }
});

async function handleSearch() {
    const matriculationNumber = document.getElementById('matriculationNumber').value.trim();
    
    if (!matriculationNumber || matriculationNumber.length !== 7) {
        showError('Please enter a valid 7-digit matriculation number');
        return;
    }
    
    if (!/^\d{7}$/.test(matriculationNumber)) {
        showError('Matriculation number must contain only digits');
        return;
    }
    
    try {
        const students = await apiCall('/students/');
        const student = students.find(s => s.matriculation_number === matriculationNumber);
        
        if (!student) {
            showError('Student not found');
            document.getElementById('studentInfo').style.display = 'none';
            document.getElementById('evaluationsContainer').style.display = 'none';
            document.getElementById('noResults').style.display = 'block';
            return;
        }
        
        await loadStudentHistory(student.id);
        displayStudentInfo(student);
        
    } catch (error) {
        console.error('Error searching for student:', error);
        showError('Failed to search for student: ' + (error.message || 'Unknown error'));
    }
}

async function loadStudentHistory(studentId) {
    try {
        const evaluations = await apiCall(`/students/${studentId}/evaluations`);
        const container = document.getElementById('evaluationsList');
        const evaluationsContainer = document.getElementById('evaluationsContainer');
        const noResults = document.getElementById('noResults');
        
        container.innerHTML = '';
        
        if (evaluations.length === 0) {
            evaluationsContainer.style.display = 'none';
            noResults.style.display = 'block';
            return;
        }
        
        noResults.style.display = 'none';
        evaluationsContainer.style.display = 'block';
        
        evaluations.forEach(evaluation => {
            const evalCard = document.createElement('div');
            evalCard.className = 'info-box';
            evalCard.style.marginBottom = '1.5rem';
            evalCard.style.padding = '1.5rem';
            
            const percentage = evaluation.max_possible_score > 0 
                ? (evaluation.total_score / evaluation.max_possible_score * 100).toFixed(2)
                : 0;
            
            const percentageColor = percentage >= 80 ? '#10b981' : percentage >= 60 ? '#f59e0b' : '#ef4444';
            const date = new Date(evaluation.created_at).toLocaleDateString('de-DE', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            evalCard.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--primary-color);">
                            <i class="fas fa-file-alt"></i> ${evaluation.report_title}
                        </h4>
                        <p style="margin: 0; color: var(--text-secondary); font-size: 0.875rem;">
                            <i class="fas fa-book"></i> ${evaluation.report_type.name}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: ${percentageColor};">
                            ${percentage}%
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            ${evaluation.total_score.toFixed(2)} / ${evaluation.max_possible_score.toFixed(2)}
                        </div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Date</div>
                        <div style="font-weight: 500;">${date}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Method</div>
                        <div style="font-weight: 500;">${evaluation.evaluation_method}</div>
                    </div>
                    ${evaluation.oberseminar_date ? `
                    <div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Oberseminar</div>
                        <div style="font-weight: 500;">${evaluation.oberseminar_date}${evaluation.oberseminar_time ? ' ' + evaluation.oberseminar_time : ''}</div>
                    </div>
                    ` : ''}
                </div>
                <div style="margin-top: 1rem;">
                    <button type="button" class="btn btn-secondary" onclick="downloadReport(${evaluation.id}, 'html')" style="margin-right: 0.5rem;">
                        <i class="fas fa-file-code"></i> HTML
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="downloadReport(${evaluation.id}, 'pdf')">
                        <i class="fas fa-file-pdf"></i> PDF
                    </button>
                </div>
            `;
            
            container.appendChild(evalCard);
        });
        
    } catch (error) {
        console.error('Error loading student history:', error);
        showError('Failed to load student history: ' + (error.message || 'Unknown error'));
    }
}

function displayStudentInfo(student) {
    const studentInfo = document.getElementById('studentInfo');
    studentInfo.innerHTML = `
        <h3 style="margin-bottom: 1rem;">
            <i class="fas fa-user-graduate"></i> ${student.first_name} ${student.last_name}
        </h3>
        <p style="margin: 0; color: var(--text-secondary);">
            <strong>Matriculation Number:</strong> ${student.matriculation_number}
        </p>
    `;
    studentInfo.style.display = 'block';
}

function downloadReport(evaluationId, format) {
    const url = `/api/evaluations/${evaluationId}/report/${format}`;
    window.open(url, '_blank');
}
