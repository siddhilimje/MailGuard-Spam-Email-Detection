import time

class DataStore:
    def __init__(self):
        self.stats = {
            "total_scans": 28412,
            "spam_detected": 4386,
            "accuracy_percent": 99.2,
            "review_queue_count": 37,
            "high_priority_queue": 8,
            "p95_latency": "1.4s",
            "uptime": "99.99%",
            "data_drift": "Low",
            "model_version": "v3.8.2"
        }
        
        # Pre-seeded with items from the prototype screenshot
        self.history = [
            {
                "id": "MG-10482",
                "subject": "Claim your cash prize now",
                "prediction": "Spam",
                "is_spam": True,
                "confidence": "98%",
                "time": "Just now",
                "sender": "winner-center@lucky-claims.xyz",
                "timestamp": time.time()
            },
            {
                "id": "MG-10481",
                "subject": "Quarterly report attached",
                "prediction": "Legitimate",
                "is_spam": False,
                "confidence": "97%",
                "time": "2 min ago",
                "sender": "finance@corp-division.internal",
                "timestamp": time.time() - 120
            },
            {
                "id": "MG-10480",
                "subject": "Urgent: verify your identity",
                "prediction": "Spam",
                "is_spam": True,
                "confidence": "94%",
                "time": "5 min ago",
                "sender": "security-alert@verification-portal.net",
                "timestamp": time.time() - 300
            },
            {
                "id": "MG-10479",
                "subject": "All-hands meeting reschedule",
                "prediction": "Legitimate",
                "is_spam": False,
                "confidence": "99%",
                "time": "14 min ago",
                "sender": "hr-operations@company.com",
                "timestamp": time.time() - 840
            },
            {
                "id": "MG-10478",
                "subject": "Wire transfer pending authorization",
                "prediction": "Spam",
                "is_spam": True,
                "confidence": "96%",
                "time": "28 min ago",
                "sender": "accounting@swift-confirm.org",
                "timestamp": time.time() - 1680
            }
        ]
        
        self.feedback_queue = [
            {
                "id": "FB-201",
                "scan_id": "MG-10480",
                "subject": "Urgent: verify your identity",
                "user_verdict": "Spam",
                "model_verdict": "Spam",
                "status": "Approved",
                "time": "10 min ago"
            },
            {
                "id": "FB-202",
                "scan_id": "MG-10476",
                "subject": "Exclusive discount promo on electronics",
                "user_verdict": "Spam",
                "model_verdict": "Legitimate",
                "status": "Pending Review",
                "time": "32 min ago"
            }
        ]
        
        # 12-hour hourly prediction volumes for chart
        self.hourly_volume = [
            {"time": "08:00", "volume": 320},
            {"time": "09:00", "volume": 480},
            {"time": "10:00", "volume": 410},
            {"time": "11:00", "volume": 690},
            {"time": "12:00", "volume": 580},
            {"time": "13:00", "volume": 720},
            {"time": "14:00", "volume": 640},
            {"time": "15:00", "volume": 810},
            {"time": "16:00", "volume": 760},
            {"time": "17:00", "volume": 890},
            {"time": "18:00", "volume": 830},
            {"time": "Now", "volume": 952}
        ]

    def add_scan(self, sender: str, subject: str, is_spam: bool, confidence: int):
        self.stats["total_scans"] += 1
        if is_spam:
            self.stats["spam_detected"] += 1
            
        new_id = f"MG-{self.stats['total_scans'] % 100000}"
        record = {
            "id": new_id,
            "subject": subject or "(No subject)",
            "prediction": "Spam" if is_spam else "Legitimate",
            "is_spam": is_spam,
            "confidence": f"{confidence}%",
            "time": "Just now",
            "sender": sender or "unknown@domain.com",
            "timestamp": time.time()
        }
        self.history.insert(0, record)
        if len(self.history) > 50:
            self.history.pop()
        return new_id

    def add_feedback(self, scan_id: str, subject: str, user_verdict: str, model_verdict: str):
        self.stats["review_queue_count"] += 1
        fb_id = f"FB-{len(self.feedback_queue) + 201}"
        entry = {
            "id": fb_id,
            "scan_id": scan_id,
            "subject": subject,
            "user_verdict": user_verdict,
            "model_verdict": model_verdict,
            "status": "Pending Review",
            "time": "Just now"
        }
        self.feedback_queue.insert(0, entry)
        return fb_id

store = DataStore()

