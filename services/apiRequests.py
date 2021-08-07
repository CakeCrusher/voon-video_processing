from github import Github

def parseGithubURL(url):
    splitURL = url.split('/')
    owner = splitURL[3]
    repo = splitURL[4]
    return {
        "owner": owner,
        "repo": repo
    }
def fetchRepoFiles(owner, repo):
    files = []
    g = Github('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')
    repo = g.get_repo(f'{owner}/{repo}')
    contents = repo.get_contents('')
    while contents:
        file_content = contents.pop(0)
        if file_content.type == 'dir':
            contents.extend(repo.get_contents(file_content.path))
        else:
            files.append(file_content.path)
    return files

# parsedUrl = parseGithubURL('https://github.com/CakeCrusher/restock_emailer')
# filePaths = fetchRepoFiles(parsedUrl['owner'], parsedUrl['repo'])
# files = [path.split('/')[-1] for path in filePaths]
# print(files)
