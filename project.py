//only commit
from flask import Flask, request, jsonify
from datetime import datetime
app = Flask(__name__)

#In-memory storage for attendance records
attendance_records = {}
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    student_id = data.get('student_id')
    class_id = data.get('class_id')
    timestamp = datetime.now().isoformat()

    if student_id and class_id:
        if class_id not in attendance_records:
            attendance_records[class_id] = []

        attendance_records[class_id].append({
            'student_id': student_id,
            'timestamp': timestamp
        })

        return jsonify({"message": "Attendance marked successfully", "timestamp": timestamp}), 201

    return jsonify({"error": "Invalid data"}), 400

@app.route('/attendance/<class_id>', methods=['GET'])
def get_attendance(class_id):
    if class_id in attendance_records:
        return jsonify(attendance_records[class_id]), 200
    return jsonify({"error": "Class ID not found"}), 404

@app.route('/attendance_report', methods=['GET'])
def attendance_report():
    class_id = request.args.get('class_id')

    if class_id in attendance_records:
        report = {}
        for record in attendance_records[class_id]:
            student_id = record['student_id']
            if student_id not in report:
                report[student_id] = 0
            report[student_id] += 1

        return jsonify(report), 200

    return jsonify({"error": "Class ID not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
