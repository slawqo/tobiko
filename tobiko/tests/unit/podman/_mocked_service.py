types = """
type ListPodData (
    id: string,
    name: string,
    createdat: string,
    cgroup: string,
    status: string,
    labels: [string]string,
    numberofcontainers: string,
    containersinfo: []ListPodContainerInfo
)
type ListPodContainerInfo (
    name: string,
    id: string,
    status: string
)
"""


class ServicePod:

    def StartPod(self, name: str) -> str:
        """return pod"""
        return {  # type: ignore
            "pod": "135d71b9495f7c3967f536edad57750bfd"
                   "b569336cd107d8aabab45565ffcfb6",
            "name": name
        }

    def GetPod(self, name: str) -> str:
        """return pod: ListPodData"""
        return {  # type: ignore
            "pod": {
                "cgroup": "machine.slice",
                "containersinfo": [
                  {
                    "id": "1840835294cf076a822e4e12ba4152411f131"
                          "bd869e7f6a4e8b16df9b0ea5c7f",
                    "name": "1840835294cf-infra",
                    "status": "running"
                  },
                  {
                    "id": "49a5cce72093a5ca47c6de86f10ad7bb36391e2"
                          "d89cef765f807e460865a0ec6",
                    "name": "upbeat_murdock",
                    "status": "running"
                  }
                ],
                "createdat": "2018-12-07 13:10:15.014139258 -0600 CST",
                "id": "135d71b9495f7c3967f536edad57750bfdb569336cd"
                      "107d8aabab45565ffcfb6",
                "name": name,
                "numberofcontainers": "2",
                "status": "Running"
            }
        }

    def GetVersion(self) -> str:
        """return version"""
        return {"version": "testing"}  # type: ignore
