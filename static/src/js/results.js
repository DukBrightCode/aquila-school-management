// static/src/js/results.js
// Fallback apiPost helper if not defined globally
const apiPost = window.apiPost || async function(url, data) {
    const getCookie = (name) => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error (${response.status})`);
    }
    return await response.json();
};

document.addEventListener('DOMContentLoaded', () => {
    const appEl = document.getElementById('score-entry-app');
    if (!appEl) return;
    const dataUrl = appEl.dataset.url;
    const subjectsUrl = appEl.dataset.subjectsUrl;
    const saveUrl = appEl.dataset.saveUrl;
    const classArmSelect = document.getElementById('filter-class-arm');
    const subjectSelect = document.getElementById('filter-subject');
    const termSelect = document.getElementById('filter-term');
    const examTypeSelect = document.getElementById('filter-exam-type');
    const tableWrap = document.getElementById('score-table-wrap');
    const saveBtn = document.getElementById('save-all-scores');
    const msgDiv = document.getElementById('score-message');
    let currentAssessmentTypes = [];
    let currentStudents = [];
    
    function showMessage(text, isError = false) {
        msgDiv.textContent = text;
        msgDiv.className = `mb-4 p-4 rounded text-sm font-medium ${
            isError ? 'bg-red-100 text-red-700 border border-red-300' : 'bg-green-100 text-green-700 border border-green-300'
        }`;
        msgDiv.classList.remove('hidden');
    }
    
    function hideMessage() {
        msgDiv.classList.add('hidden');
    }

    async function fetchSubjectsForClass() {
        const classArm = classArmSelect.value;
        if (!classArm) {
            subjectSelect.innerHTML = '<option value="">-- Select Class First --</option>';
            subjectSelect.disabled = true;
            return;
        }

        try {
            const query = new URLSearchParams({ class_arm: classArm });
            const data = await apiGet(`${subjectsUrl}?${query.toString()}`);
            const subjects = data.subjects || [];

            if (subjects.length === 0) {
                subjectSelect.innerHTML = '<option value="">-- No Subjects Assigned --</option>';
                subjectSelect.disabled = true;
                showMessage('No subjects are assigned to this class. Please contact the class teacher or administrator.', true);
            } else {
                subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
                subjects.forEach(sub => {
                    subjectSelect.innerHTML += `<option value="${sub.id}">${sub.name} (${sub.code})</option>`;
                });
                subjectSelect.disabled = false;
                hideMessage();
            }
        } catch (err) {
            subjectSelect.innerHTML = '<option value="">-- Error Loading Subjects --</option>';
            subjectSelect.disabled = true;
            showMessage(err.message || 'Failed to fetch subjects for this class.', true);
        }
    }

    async function fetchScoreGrid() {
        const classArm = classArmSelect.value;
        const subject = subjectSelect.value;
        const term = termSelect.value;
        const examType = examTypeSelect.value;
        hideMessage();
        if (!classArm || !subject || !term || !examType) {
            tableWrap.innerHTML = '<p class="p-4 text-gray-500 italic">Select Class Arm, Subject, Term, and Exam Type to load assessment grid.</p>';
            saveBtn.classList.add('hidden');
            return;
        }
        try {
            const query = new URLSearchParams({ class_arm: classArm, subject: subject, term: term, exam_type: examType });
            const data = await apiGet(`${dataUrl}?${query.toString()}`);
            currentAssessmentTypes = data.assessment_types || [];
            currentStudents = data.students || [];
            const scores = data.scores || {};
            if (currentAssessmentTypes.length === 0) {
                tableWrap.innerHTML = '<p class="p-4 text-amber-600">No active assessment components configured for this term.</p>';
                saveBtn.classList.add('hidden');
                return;
            }
            if (currentStudents.length === 0) {
                tableWrap.innerHTML = '<p class="p-4 text-gray-500">No students enrolled in the selected class arm.</p>';
                saveBtn.classList.add('hidden');
                return;
            }
            renderGrid(scores);
            saveBtn.classList.remove('hidden');
        } catch (err) {
            showMessage(err.message || 'Failed to fetch score entry data.', true);
        }
    }

    function renderGrid(scores) {
        let html = `
            <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-3 text-left font-semibold text-gray-600">Admission No.</th>
                        <th class="px-4 py-3 text-left font-semibold text-gray-600">Student Name</th>
        `;
        currentAssessmentTypes.forEach(at => {
            html += `<th class="px-4 py-3 text-center font-semibold text-gray-600">${at.name}<br><span class="text-xs text-gray-400">(Max ${at.max_score} | ${at.weight_percentage}%)</span></th>`;
        });
        html += `
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
        `;
        currentStudents.forEach(st => {
            html += `
                <tr data-student-id="${st.id}">
                    <td class="px-4 py-3 text-gray-800 font-medium">${st.admission_number}</td>
                    <td class="px-4 py-3 text-gray-800">${st.full_name}</td>
            `;
            currentAssessmentTypes.forEach(at => {
                const key = `${st.id}-${at.id}`;
                const val = scores[key] !== undefined ? scores[key] : '';
                html += `
                    <td class="px-4 py-3 text-center">
                        <input type="number" 
                               step="0.01" 
                               max="${at.max_score}" 
                               min="0"
                               data-assessment-id="${at.id}"
                               value="${val}" 
                               class="score-input w-20 text-center border border-gray-300 rounded p-1 focus:ring-blue-500 focus:border-blue-500">
                    </td>
                `;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
        tableWrap.innerHTML = html;
    }

    // Real-time input validation as the user types
    tableWrap.addEventListener('input', (e) => {
        if (e.target.classList.contains('score-input')) {
            const input = e.target;
            const val = parseFloat(input.value);
            const atId = input.dataset.assessmentId;
            const assessmentType = currentAssessmentTypes.find(at => String(at.id) === String(atId));
            const maxScore = assessmentType ? parseFloat(assessmentType.max_score) : parseFloat(input.max);

            if (!isNaN(maxScore) && val > maxScore) {
                input.classList.add('border-red-500', 'bg-red-50', 'text-red-900');
            } else {
                input.classList.remove('border-red-500', 'bg-red-50', 'text-red-900');
            }
        }
    });

    async function saveAllScores() {
        hideMessage();
        let validationError = null;
        const rows = [];
        const studentTrs = tableWrap.querySelectorAll('tr[data-student-id]');

        studentTrs.forEach(tr => {
            const studentId = tr.dataset.studentId;
            const scoreInputs = tr.querySelectorAll('.score-input');
            const scoresObj = {};

            scoreInputs.forEach(input => {
                const atId = input.dataset.assessmentId;
                const valStr = input.value.trim();
                
                if (valStr !== '') {
                    const val = parseFloat(valStr);
                    const assessmentType = currentAssessmentTypes.find(at => String(at.id) === String(atId));
                    const maxScore = assessmentType ? parseFloat(assessmentType.max_score) : parseFloat(input.max);

                    // Check limits before sending
                    if (!isNaN(maxScore) && val > maxScore) {
                        validationError = `Score (${val}) cannot exceed the maximum limit of ${maxScore} for "${assessmentType ? assessmentType.name : 'this assessment'}".`;
                        input.classList.add('border-red-500', 'bg-red-50');
                    } else if (!isNaN(val) && val < 0) {
                        validationError = `Score cannot be less than 0.`;
                        input.classList.add('border-red-500', 'bg-red-50');
                    } else {
                        input.classList.remove('border-red-500', 'bg-red-50');
                        scoresObj[atId] = val;
                    }
                }
            });

            rows.push({
                student_id: parseInt(studentId),
                scores: scoresObj
            });
        });

        // Block request if any validation rule fails
        if (validationError) {
            showMessage(validationError, true);
            return;
        }

        const payload = {
            class_arm_id: parseInt(classArmSelect.value),
            subject_id: parseInt(subjectSelect.value),
            term_id: parseInt(termSelect.value),
            exam_type: examTypeSelect.value,
            rows: rows
        };

        try {
            const res = await apiPost(saveUrl, payload);
            showMessage(`Successfully saved ${res.saved} assessment score record(s).`);
        } catch (err) {
            showMessage(err.message || 'Error occurred while saving scores.', true);
        }
    }

    classArmSelect.addEventListener('change', () => {
        subjectSelect.value = '';
        subjectSelect.disabled = true;
        fetchSubjectsForClass();
        tableWrap.innerHTML = '<p class="p-4 text-gray-500 italic">Select Class Arm, Subject, Term, and Exam Type to load assessment grid.</p>';
        saveBtn.classList.add('hidden');
    });

    [subjectSelect, termSelect, examTypeSelect].forEach(select => {
        select.addEventListener('change', fetchScoreGrid);
    });

    saveBtn.addEventListener('click', saveAllScores);

    // Load subjects if a class is already selected
    if (classArmSelect.value) {
        fetchSubjectsForClass();
    }
});