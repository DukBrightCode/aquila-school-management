document.addEventListener('DOMContentLoaded', () => {
    const attendanceForm = document.getElementById('attendance-submit-form');
    const responseMessage = document.getElementById('response-message');

    if (!attendanceForm) return;

    attendanceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const classArmId = document.getElementById('class_arm_id').value;
        const date = document.getElementById('attendance_date').value;
        const rows = document.querySelectorAll('.student-attendance-row');

        if (!classArmId || !date) {
            alert('Class Arm and Date are required.');
            return;
        }

        const records = [];

        rows.forEach(row => {
            const studentId = row.dataset.studentId;
            const selectedStatus = row.querySelector(`input[name="status_${studentId}"]:checked`);

            if (selectedStatus) {
                records.push({
                    student_id: parseInt(studentId, 10),
                    status: selectedStatus.value
                });
            }
        });

        if (records.length === 0) {
            alert('No student attendance records selected.');
            return;
        }

        const payload = {
            class_arm_id: parseInt(classArmId, 10),
            date: date,
            records: records
        };

        const submitBtn = document.getElementById('save-attendance-btn');
        submitBtn.disabled = true;
        submitBtn.innerText = 'Saving...';

        try {
            const response = await apiRequest('/attendance/mark/', {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (response.status === 'success') {
                responseMessage.className = 'mt-4 p-3 rounded-md bg-green-100 text-green-800 text-sm font-medium';
                responseMessage.innerText = response.message;
                responseMessage.classList.remove('hidden');
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            responseMessage.className = 'mt-4 p-3 rounded-md bg-red-100 text-red-800 text-sm font-medium';
            responseMessage.innerText = error.message || 'An error occurred while saving attendance.';
            responseMessage.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Save Attendance';
        }
    });
});