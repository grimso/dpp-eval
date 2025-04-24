from dataclasses import dataclass,field
import datetime
from urllib.parse import urlparse
from github import Github,Repository
import requests

def get_github_project_name_from_url(url:str): 
    parse_result = urlparse(url)

    if parse_result.netloc != "github.com":
        return False, ""
    url_path = parse_result.path
    url_path=url_path.strip("/")
    return True, url_path



@dataclass
class Result:
    name: str = field(default="")
    full_name:str = field(default="")
    description:str = field(default="")
    homepage:str = field(default="")
    archived:bool = field(default=False)
    stargazers_count:int = field(default=-1)
    topics:list[str]=field(default_factory=list)
    languages:dict[str:int]=field(default_factory=dict)
    updated_at:str = field(default="")
    created_at:str = field(default="")
    forks_count:int = field(default=-1)
    subscribers_count:int = field(default=-1)
    contributors_count:int = field(default=-1)
    release_count:int = field(default=-1)
    latest_release_name:str = field(default="")
    latest_release_date:str = field(default="")
    license_name:str = field(default="")
    commits_count:int = field(default=-1)
    latest_tag_name:str = field(default="")
    tags_count: int = field(default=-1)
    latest_tag_date:str = field(default="")
    latest_event_date:str = field(default="")
    last_commit_date_main:str = field(default="")
    readme:str  = field(default="")
    raw_data:dict =field(default_factory=dict)
    request_date:str = field(default="")


def get_project_infromation(git_hub:Github,github_project_name:str):
    repo:Repository = git_hub.get_repo(github_project_name)

    project_info = Result()
    project_info.raw_data=repo.raw_data
    project_info.request_date=repo.raw_headers["date"]
    project_info.name=repo.name
    project_info.homepage=repo.homepage
    project_info.full_name= repo.full_name
    project_info.description = repo.description
    project_info.archived = repo.archived
    project_info.stargazers_count = repo.stargazers_count
    project_info.topics = repo.get_topics()
    project_info.languages = repo.get_languages()
    project_info.updated_at = repo.updated_at.isoformat()
    project_info.created_at = repo.created_at.isoformat()
    project_info.forks_count = repo.forks_count
    project_info.subscribers_count = repo.subscribers_count


    #collaborators = repo.get_collaborators()
    # only working for repositories owned by organizations ? 
    #info_dict["collaborators.totalCount"] =collaborators.totalCount
    contributors = repo.get_contributors()
    project_info.contributors_count = contributors.totalCount
    ## release
    from github import UnknownObjectException
    release_count=repo.get_releases().totalCount
    project_info.release_count=release_count
    if release_count:
        try: 
            release_latest=repo.get_latest_release()
            project_info.latest_release_date = release_latest.created_at.isoformat()
            project_info.latest_release_name = release_latest.tag_name
        except UnknownObjectException as e :
            pass
    

    try:
        project_info.license_name= repo.get_license().license.name
    except UnknownObjectException as e:
        pass
    
    
    ## nr commits
    project_info.commits_count = repo.get_commits().totalCount

    ## latest tag
    tags = repo.get_tags()
    project_info.tags_count = tags.totalCount
    if tags.totalCount:
        tag_latest=tags[0]
        # tag_latest.last_modified --> does not return the correct date when compared with GitHup Web UI
        project_info.latest_tag_name=tag_latest.name
        tag_latest_commit = tag_latest.commit
        project_info.latest_tag_date = tag_latest_commit.raw_data["commit"]["committer"]["date"]

    ## latest event
    events = repo.get_events()
    if events.totalCount:
        latest_event_time_raw=events.get_page(page=0)[0].last_modified
        project_info.latest_event_date = datetime.datetime.strptime(latest_event_time_raw, "%a, %d %b %Y %X %Z").isoformat()
    #latest commit to default branch
    branch = repo.get_branch(branch=repo.default_branch)
    branch.name
    project_info.last_commit_date_main = branch.commit.raw_data["commit"]["committer"]["date"]
    try:
        content_file=repo.get_readme()
        project_info.readme = content_file.decoded_content.decode()
    except Exception as e:
        pass
    return project_info


# data quality ------ 
def get_status_for_url(web_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'}
        response=requests.get(web_url,timeout=3,headers=headers)
        status=response.status_code
        return True, status
    except Exception as e:
        return False ,e 

def error_status_or_exception(tuple_is_exception_status_code):
    if not isinstance(tuple_is_exception_status_code,tuple):
        return tuple_is_exception_status_code
    is_not_exception,status_code= tuple_is_exception_status_code
    if not is_not_exception:
        return True
    if not isinstance(status_code,int):
        return True
    if status_code not in set([200,403,500]):
         return True
    return False