import requests

try:
    print("Sending request...")
    # Need valid dummy files
    with open('dummy.docx', 'wb') as f: f.write(b'dummy')
    with open('dummy.pdf', 'wb') as f: f.write(b'dummy')
    
    files = {
        'scheme': open('dummy.docx', 'rb'),
        'student_pdf': open('dummy.pdf', 'rb')
    }
    data = {'grading_mode': 'experienced'}
    
    r = requests.post("http://127.0.0.1:5000/api/grade", files=files, data=data)
    print("Response Code:", r.status_code)
    print("Response Text:", r.text)
except Exception as e:
    print("Request failed:", str(e))
