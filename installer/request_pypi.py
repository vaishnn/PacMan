from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import requests

def requestInfo(API_ENDPOINT, timeout = 10) -> dict:
    try:
        response = requests.get(API_ENDPOINT, timeout=timeout)
        if response.status_code == 200:
            response_json = response.json()
            response_json['response'] = 200
            return response_json
        else:
            # print(f"Request failed with status code {response.status_code}")
            return {'response': 404}
    except ConnectionError:
        return {'response': 500}
    except TimeoutError:
        return {'response': 504}
    except Exception: #Implement a custom logger
        return {'response': 500}

class RequestDetails(QObject):

    fetchedDetails = pyqtSignal(str, dict)
    fetchDetails = pyqtSignal(str, str)
    def __init__(self, parent=None, TIMEOUT: int = 1000):
        super().__init__(parent)


        # Thread
        self.threadR = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.threadR)
        self.fetchDetails.connect(self.worker.run)
        self.worker.finished.connect(self.return_fetched_details)
        self.threadR.finished.connect(self.deleteLater)
        self.threadR.start()

    def return_fetched_details(self, library: str, details: dict):
        self.fetchedDetails.emit(library, details)


    def fetch_details(self, API_ENDPOINT: str, library: str):
        self.fetchDetails.emit(API_ENDPOINT, library)

    def stopThread(self):
        self.threadR.quit()
        self.threadR.wait()


class Worker(QObject):
    finished = pyqtSignal(str, dict)

    @staticmethod
    def subsetData(details: dict, information_retrieve:list = [
        "summary",
        "author",
        "description",
        "name",
        "version",
        "package_url",
        "license",
        "project_urls",
        "provides_extra",
        "requires_python",
        "requires_dist",
    ]):
        final_details = {}
        for key in information_retrieve:
            if key in details.get("info", {}):
                final_details[key] = details["info"][key]

        final_details['response'] = details['response']
        return final_details

    @pyqtSlot(str, str)
    def run(self, API_ENDPOINT: str, library: str):
        details = requestInfo(API_ENDPOINT.format(library))
        if details.get('response') == 200:
            final_details = self.subsetData(details)
        else:
            final_details = details
        self.finished.emit(library, final_details)

if __name__ == "__main__":
    # Implement Test Class
    pass
