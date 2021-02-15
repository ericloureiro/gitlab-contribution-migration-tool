
# Contribution Migration Tool

Contribution Migration Tool is a script to migrate all contributions done on  **GitLab**  to  **GitHub**.

> **Disclaimer**: this script **does not** completely migrates your commits, it **mimics** every contribution made on GitLab into a **generic commit** on the same date.


## [](https://github.com/ericloureiro/gitlab-contribution-migration-tool/blob/main/README.md#get-started)Get Started

Before running the script you need to make: 
- A  **public profile**  on GitLab;
- A  **private repository**  on GitHub.

Then: 
- Clone  **your**  repository to local;
- Copy  `gitlab-migrator.py`  into your project folder; 
- Run  `python3 migrator.py <username> [initialDate]`; 
	> - username: profile user on GitLab; 
	>  - initialDate(optional): Start commit date in YYYY-MM-DD format. Do not inform it for all commits. 
		
		If this is not your first time using this script on the same repository, there is no need
        to inform a date since contributions are handled automatically to prevent duplicated commits.
- Push your commits; 
- Enjoy your calendar contributions on both platforms!

## Demonstration

![](demo.gif)

### [](https://github.com/ericloureiro/gitlab-contribution-migration-tool/blob/main/README.md#many-thanks-to-ssk1002-for-original-idea)Many thanks to  [ssk1002](https://github.com/ssk1002/gitlab-contribution-migration-tool)  for the original idea
