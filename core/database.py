import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='data/analytics.db'):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                total_max INTEGER NOT NULL,
                grading_mode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id INTEGER NOT NULL,
                q_num INTEGER NOT NULL,
                question_text TEXT,
                score INTEGER NOT NULL,
                max_marks INTEGER NOT NULL,
                match_percentage REAL,
                FOREIGN KEY (evaluation_id) REFERENCES evaluations (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_evaluation(self, exam_id, student_id, total_score, total_max, grading_mode, results):
        """
        Saves a single student's evaluation to the database.
        results is a list of question result dicts.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. Insert evaluation
        cursor.execute('''
            INSERT INTO evaluations (exam_id, student_id, total_score, total_max, grading_mode)
            VALUES (?, ?, ?, ?, ?)
        ''', (exam_id, student_id, total_score, total_max, grading_mode))
        
        evaluation_id = cursor.lastrowid
        
        # 2. Insert question scores
        for res in results:
            if not res: continue
            cursor.execute('''
                INSERT INTO question_scores (evaluation_id, q_num, question_text, score, max_marks, match_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                evaluation_id,
                res.get('q_num', 0),
                res.get('question', ''),
                res.get('score', 0),
                res.get('max_marks', 0),
                res.get('match', 0.0)
            ))
            
        conn.commit()
        conn.close()
        return evaluation_id

    def get_analytics_summary(self, exam_id=None):
        """
        Returns a dictionary with high-level analytics.
        If exam_id is provided, filters by that exam. Otherwise returns all-time stats.
        """
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query_filter = "WHERE exam_id = ?" if exam_id else ""
        params = (exam_id,) if exam_id else ()
        
        # 1. Overall Stats
        cursor.execute(f'''
            SELECT 
                COUNT(id) as total_submissions,
                AVG(CAST(total_score AS FLOAT) / total_max) * 100 as class_average,
                MAX(CAST(total_score AS FLOAT) / total_max) * 100 as highest_score,
                MIN(CAST(total_score AS FLOAT) / total_max) * 100 as lowest_score
            FROM evaluations
            {query_filter}
            AND total_max > 0
        ''', params)
        
        stats_row = cursor.fetchone()
        
        # 1.5 Get USNs for highest and lowest
        cursor.execute(f'''
            SELECT student_id, CAST(total_score AS FLOAT) / total_max as pct
            FROM evaluations
            {query_filter}
            AND total_max > 0
            ORDER BY pct DESC, created_at DESC
            LIMIT 1
        ''', params)
        highest_row = cursor.fetchone()
        highest_usn = highest_row['student_id'] if highest_row else None
        
        cursor.execute(f'''
            SELECT student_id, CAST(total_score AS FLOAT) / total_max as pct
            FROM evaluations
            {query_filter}
            AND total_max > 0
            ORDER BY pct ASC, created_at DESC
            LIMIT 1
        ''', params)
        lowest_row = cursor.fetchone()
        lowest_usn = lowest_row['student_id'] if lowest_row else None
        
        # 2. Question Difficulty Analysis
        # We join evaluations to ensure we respect the exam_id filter
        cursor.execute(f'''
            SELECT 
                q.q_num,
                q.question_text,
                AVG(CAST(q.score AS FLOAT) / q.max_marks) * 100 as avg_score_pct
            FROM question_scores q
            JOIN evaluations e ON q.evaluation_id = e.id
            {query_filter}
            AND q.max_marks > 0
            GROUP BY q.q_num, q.question_text
            ORDER BY avg_score_pct ASC
        ''', params)
        
        questions_row = cursor.fetchall()
        conn.close()
        
        if not stats_row or stats_row['total_submissions'] == 0:
            return {
                "total_submissions": 0,
                "class_average": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "highest_score_usn": None,
                "lowest_score_usn": None,
                "hardest_questions": []
            }
            
        return {
            "total_submissions": stats_row['total_submissions'],
            "class_average": round(stats_row['class_average'] or 0, 1),
            "highest_score": round(stats_row['highest_score'] or 0, 1),
            "lowest_score": round(stats_row['lowest_score'] or 0, 1),
            "highest_score_usn": highest_usn,
            "lowest_score_usn": lowest_usn,
            "hardest_questions": [
                {
                    "q_num": row['q_num'],
                    "question": row['question_text'],
                    "avg_score_pct": round(row['avg_score_pct'] or 0, 1)
                }
                for row in questions_row
            ]
        }
