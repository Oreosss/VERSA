# Retrieval Validation Log (Stage 6a)

Retrieval-only validation. Does not assess prompts or generated summaries.

## Interpretation (plain language)

Confirmed: none of the 24 eval CVE ids are present in the `rag_corpus` collection. The eval sample and the retrieval corpus are strictly distinct.

Nearest-neighbour distance across the 24 eval CVEs ranges from 0.0068 to 0.6224 (median 0.3418, 75th percentile 0.4032). 6 eval CVE(s) sit above the 75th percentile on nearest-neighbour distance and are flagged below as candidates for closer manual review -- this is a statistical prompt for attention, not a pass/fail judgement. Whether these CVEs are actually poorly grounded depends on the manual same-class relevance read in the per-CVE sections, not on distance alone.

Flagged for review (nearest-neighbour distance above cohort 75th percentile):
- CVE-2020-8010 (CRITICAL, cell A) -- nearest-neighbour distance 0.4324
- CVE-2023-29119 (CRITICAL, cell A) -- nearest-neighbour distance 0.6224
- CVE-2020-8958 (HIGH, cell C) -- nearest-neighbour distance 0.4206
- CVE-2023-43661 (HIGH, cell C) -- nearest-neighbour distance 0.5411
- CVE-2020-8655 (HIGH, cell D) -- nearest-neighbour distance 0.5283
- CVE-2022-40765 (MEDIUM, cell F) -- nearest-neighbour distance 0.4328

Coverage is assessed against the severity x exploitability grid the eval sample was deliberately designed on, not against the corpus's severity proportions -- the eval sample is not meant to mirror the corpus, so proportional resemblance is not the test applied here. The grid populated below should be checked for empty or overloaded cells.

This file presents evidence only. It does not compute or state an overall pass/fail verdict for retrieval quality or eval sample quality -- that judgement is made by the reviewer using the per-CVE manual relevance blanks below plus the coverage grid.

## Setup checks

- Eval sample: `data/eval_sample.jsonl`, 24 records, fields confirmed (`id`, `description`, `cvss_severity`).
- Corpus collection: `rag_corpus` at `data/chroma_db`, 11976 documents.
- Distinctness: PASSED, 0 overlapping ids.
- Embedding model: `all-MiniLM-L6-v2` (matches corpus-build model in `src/chroma_ingest.py`). General-purpose, not security-domain-tuned -- cosine distance is a rough signal, not ground truth, which is why the manual same-class judgement below carries real weight.

## Grounding: per-CVE detail and manual judgement

Read the target description, read each neighbour's description, and record whether they describe the same class of vulnerability. Descriptions are printed in full (not truncated).

### CVE-2020-8010  [CRITICAL, cell A, KEV=False, EPSS=0.48665]

**TARGET:** CA Unified Infrastructure Management (Nimsoft/UIM) 20.1, 20.3.x, and 9.20 and below contains an improper ACL handling vulnerability in the robot (controller) component. A remote attacker can execute commands, read from, or write to the target system.

nearest-neighbour distance: 0.4324  |  mean top-5 distance: 0.4842  |  max top-5 distance: 0.5036

**Neighbour 1**  |  dist 0.4324  |  MEDIUM  |  corpus-id CVE-2024-1914

> An attacker who successfully exploited these vulnerabilities could cause the robot to stop, make the robot controller inaccessible.  

The vulnerability could potentially be exploited to perform unauthorized actions by an attacker. This vulnerability arises under specific condition when specially crafted message is processed by the system. 

Below are reported vulnerabilities in the Robot Ware versions. 

* IRC5- RobotWare 6 < 6.15.06 except 6.10.10, and 6.13.07 
* OmniCore- RobotWare 7 < 7.14

**Neighbour 2**  |  dist 0.4885  |  MEDIUM  |  corpus-id CVE-2025-0571

> Sante PACS Server Web Portal DCM File Parsing Memory Corruption Denial-of-Service Vulnerability. This vulnerability allows remote attackers to create a denial-of-service condition on affected installations of Sante PACS Server. Authentication is required to exploit this vulnerability.

The specific flaw exists within the parsing of DCM files. The issue results from the lack of proper validation of user-supplied data, which can result in a memory corruption condition. An attacker can leverage this vulnerability to create a denial-of-service condition on the system. Was ZDI-CAN-25305.

**Neighbour 3**  |  dist 0.4982  |  HIGH  |  corpus-id CVE-2024-30961

> Insecure Permissions vulnerability in Open Robotics Robotic Operating System 2 (ROS2) navigation2- ROS2-humble and navigation 2-humble allows a local attacker to execute arbitrary code via the error-thrown mechanism in nav2_bt_navigator.

**Neighbour 4**  |  dist 0.4982  |  MEDIUM  |  corpus-id CVE-2020-3371

> A vulnerability in the web UI of Cisco Integrated Management Controller (IMC) could allow an authenticated, remote attacker to inject arbitrary code and execute arbitrary commands at the underlying operating system level. The vulnerability is due to insufficient input validation. An attacker could exploit this vulnerability by sending crafted commands to the web-based management interface of the affected software. A successful exploit could allow the attacker to inject and execute arbitrary commands at the underlying operating system level.

**Neighbour 5**  |  dist 0.5036  |  MEDIUM  |  corpus-id CVE-2023-40686

> Management Central as part of IBM i 7.2, 7.3, 7.4, and 7.5 Navigator contains a local privilege escalation vulnerability.  A malicious actor with command line access to the operating system can exploit this vulnerability to elevate privileges to gain component access to the operating system.  IBM X-Force ID:  264114.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-50919  [CRITICAL, cell A, KEV=False, EPSS=0.47804]

**TARGET:** An issue was discovered on GL.iNet devices before version 4.5.0. There is an NGINX authentication bypass via Lua string pattern matching. This affects A1300 4.4.6, AX1800 4.4.6, AXT1800 4.4.6, MT3000 4.4.6, MT2500 4.4.6, MT6000 4.5.0, MT1300 4.3.7, MT300N-V2 4.3.7, AR750S 4.3.7, AR750 4.3.7, AR300M 4.3.7, and B1300 4.3.7.

nearest-neighbour distance: 0.3974  |  mean top-5 distance: 0.4861  |  max top-5 distance: 0.5293

**Neighbour 1**  |  dist 0.3974  |  CRITICAL  |  corpus-id CVE-2024-39227

> GL-iNet products AR750/AR750S/AR300M/AR300M16/MT300N-V2/B1300/MT1300/SFT1200/X750 v4.3.11, MT3000/MT2500/AXT1800/AX1800/A1300/X300B v4.5.16, XE300 v4.3.16, E750 v4.3.12, AP1300/S1300 v4.3.13, and XE3000/X3000 v4.4 were discovered to contain insecure permissions in the endpoint /cgi-bin/glc. This vulnerability allows unauthenticated attackers to execute arbitrary code or possibly a directory traversal via crafted JSON data.

**Neighbour 2**  |  dist 0.4632  |  CRITICAL  |  corpus-id CVE-2023-29778

> GL.iNET MT3000 4.1.0 Release 2 is vulnerable to OS Command Injection via /usr/lib/oui-httpd/rpc/logread.

**Neighbour 3**  |  dist 0.5169  |  MEDIUM  |  corpus-id CVE-2023-52534

> In ngmm, there is a possible undefined behavior due to incorrect error handling. This could lead to remote denial of service with no additional execution privileges needed

**Neighbour 4**  |  dist 0.5237  |  MEDIUM  |  corpus-id CVE-2024-7554

> An issue has been discovered in GitLab CE/EE affecting all versions starting from 13.9 before 17.0.6, all versions starting from 17.1 before 17.1.4, all versions starting from 17.2 before 17.2.2. Under certain conditions, access tokens may have been logged when an API request was made in a specific manner.

**Neighbour 5**  |  dist 0.5293  |  HIGH  |  corpus-id CVE-2021-45575

> Certain NETGEAR devices are affected by command injection by an authenticated user. This affects RBK752 before 3.2.16.6, RBR750 before 3.2.16.6, RBS750 before 3.2.16.6, RBK852 before 3.2.16.6, RBR850 before 3.2.16.6, and RBS850 before 3.2.16.6.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-29119  [CRITICAL, cell A, KEV=False, EPSS=0.00326]

**TARGET:** Waybox Enel X web management application could execute arbitrary requests on the internal database via /admin/dbstore.php.

nearest-neighbour distance: 0.6224  |  mean top-5 distance: 0.6277  |  max top-5 distance: 0.6324

**Neighbour 1**  |  dist 0.6224  |  CRITICAL  |  corpus-id CVE-2020-23763

> SQL injection in admin.php in Online Book Store 1.0 allows remote attackers to execute arbitrary SQL commands and bypass authentication.

**Neighbour 2**  |  dist 0.6254  |  MEDIUM  |  corpus-id CVE-2025-63947

> A Reflected Cross-Site Scripting (XSS) vulnerability exists in phpMsAdmin version 2.2 in the database_mode.php file. An attacker can execute arbitrary web script or HTML via the dbname parameter after a user is authenticated.

**Neighbour 3**  |  dist 0.6277  |  MEDIUM  |  corpus-id CVE-2024-40741

> A cross-site scripting (XSS) vulnerability in netbox v4.0.3 allows attackers to execute arbitrary web scripts or HTML via a crafted payload injected into the circuit ID parameter at /circuits/circuits/{id}/edit/.

**Neighbour 4**  |  dist 0.6308  |  MEDIUM  |  corpus-id CVE-2023-33787

> A stored cross-site scripting (XSS) vulnerability in the Create Tenant Groups (/tenancy/tenant-groups/) function of Netbox v3.5.1 allows attackers to execute arbitrary web scripts or HTML via a crafted payload injected into the Name field.

**Neighbour 5**  |  dist 0.6324  |  MEDIUM  |  corpus-id CVE-2024-6263

> The WP Lightbox 2 plugin for WordPress is vulnerable to Stored Cross-Site Scripting via the ‘title’ parameter in all versions up to, and including, 3.0.6.6 due to insufficient input sanitization and output escaping. This makes it possible for authenticated attackers, with Contributor-level access and above, to inject arbitrary web scripts in pages that will execute whenever a user accesses an injected page.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-23894  [CRITICAL, cell A, KEV=False, EPSS=0.02242]

**TARGET:** Deserialization of untrusted data vulnerability in McAfee Database Security (DBSec) prior to 4.8.2 allows a remote unauthenticated attacker to create a reverse shell with administrator privileges on the DBSec server via carefully constructed Java serialized object sent to the DBSec server.

nearest-neighbour distance: 0.2549  |  mean top-5 distance: 0.3704  |  max top-5 distance: 0.4213

**Neighbour 1**  |  dist 0.2549  |  LOW  |  corpus-id CVE-2021-23896

> Cleartext Transmission of Sensitive Information vulnerability in the administrator interface of McAfee Database Security (DBSec) prior to 4.8.2 allows an administrator to view the unencrypted password of the McAfee Insights Server used to pass data to the Insights Server. This user is restricted to only have access to DBSec data in the Insights Server.

**Neighbour 2**  |  dist 0.3757  |  MEDIUM  |  corpus-id CVE-2020-7325

> Privilege Escalation vulnerability in McAfee MVISION Endpoint prior to 20.9 Update allows local users to access files which the user otherwise would not have access to via manipulating symbolic links to redirect McAfee file operations to an unintended file.

**Neighbour 3**  |  dist 0.3986  |  HIGH  |  corpus-id CVE-2020-7331

> Unquoted service executable path in McAfee Endpoint Security (ENS) prior to 10.7.0 November 2020 Update allows local users to cause a denial of service and malicious file execution via carefully crafted and named executable files.

**Neighbour 4**  |  dist 0.4016  |  HIGH  |  corpus-id CVE-2020-7264

> Privilege Escalation vulnerability in McAfee Endpoint Security (ENS) for Windows prior to 10.7.0 Hotfix 199847 allows local users to delete files the user would otherwise not have access to via manipulating symbolic links to redirect a McAfee delete action to an unintended file. This is achieved through running a malicious script or program on the target machine.

**Neighbour 5**  |  dist 0.4213  |  MEDIUM  |  corpus-id CVE-2021-31842

> XML Entity Expansion injection vulnerability in McAfee Endpoint Security (ENS) for Windows prior to 10.7.0 September 2021 Update allows a local user to initiate high CPU and memory consumption resulting in a Denial of Service attack through carefully editing the EPDeploy.xml file and then executing the setup process.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2024-21887  [CRITICAL, cell B, KEV=True, EPSS=0.99999]

**TARGET:** A command injection vulnerability in web components of Ivanti Connect Secure (9.x, 22.x) and Ivanti Policy Secure (9.x, 22.x)  allows an authenticated administrator to send specially crafted requests and execute arbitrary commands on the appliance.

nearest-neighbour distance: 0.1900  |  mean top-5 distance: 0.2826  |  max top-5 distance: 0.3585

**Neighbour 1**  |  dist 0.1900  |  CRITICAL  |  corpus-id CVE-2024-10644

> Code injection in Ivanti Connect Secure before version 22.7R2.4 and Ivanti Policy Secure before version 22.7R1.3 allows a remote authenticated attacker with admin privileges to achieve remote code execution.

**Neighbour 2**  |  dist 0.2486  |  MEDIUM  |  corpus-id CVE-2024-47905

> A stack-based buffer overflow in Ivanti Connect Secure before version 22.7R2.3 and Ivanti Policy Secure before version 22.7R1.2 allows a remote authenticated attacker with admin privileges to cause a denial of service.

**Neighbour 3**  |  dist 0.3065  |  HIGH  |  corpus-id CVE-2024-24994

> A Path Traversal vulnerability in web component of Ivanti Avalanche before 6.4.3 allows a remote authenticated attacker to execute arbitrary commands as SYSTEM. 

**Neighbour 4**  |  dist 0.3097  |  MEDIUM  |  corpus-id CVE-2025-55146

> An unchecked return value in Ivanti Connect Secure before 22.7R2.9 or 22.8R2, Ivanti Policy Secure before 22.7R1.6, Ivanti ZTA Gateway before 2.8R2.3-723 and Ivanti Neurons for Secure Access before 22.8R1.4 (Fix deployed on 02-Aug-2025) allows a remote authenticated attacker with admin privileges to trigger a denial of service.

**Neighbour 5**  |  dist 0.3585  |  HIGH  |  corpus-id CVE-2025-55148

> Missing authorization in Ivanti Connect Secure before 22.7R2.9 or 22.8R2, Ivanti Policy Secure before 22.7R1.6, Ivanti ZTA Gateway before 2.8R2.3-723 and Ivanti Neurons for Secure Access before 22.8R1.4 (Fix deployed on 02-Aug-2025) allows a remote authenticated attacker with read-only admin privileges to configure restricted settings.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-26084  [CRITICAL, cell B, KEV=True, EPSS=0.99999]

**TARGET:** In affected versions of Confluence Server and Data Center, an OGNL injection vulnerability exists that would allow an unauthenticated attacker to execute arbitrary code on a Confluence Server or Data Center instance. The affected versions are before version 6.13.23, from version 6.14.0 before 7.4.11, from version 7.5.0 before 7.11.6, and from version 7.12.0 before 7.12.5.

nearest-neighbour distance: 0.2461  |  mean top-5 distance: 0.2984  |  max top-5 distance: 0.3645

**Neighbour 1**  |  dist 0.2461  |  HIGH  |  corpus-id CVE-2021-43940

> Affected versions of Atlassian Confluence Server and Data Center allow authenticated local attackers to achieve elevated privileges on the local system via a DLL Hijacking vulnerability in the Confluence installer. This vulnerability only affects installations of Confluence Server and Data Center on Windows. The affected versions are before version 7.4.10, and from version 7.5.0 before 7.12.3.

**Neighbour 2**  |  dist 0.2689  |  HIGH  |  corpus-id CVE-2023-22512

> This High severity DoS (Denial of Service) vulnerability was introduced in version 5.6.0 of Confluence Data Center and Server. With a CVSS Score of 7.5, this vulnerability allows an unauthenticated attacker to cause a resource to be unavailable for its intended users by temporarily or indefinitely disrupting services of a vulnerable host (Confluence instance) connected to a network, which has no impact to confidentiality, no impact to integrity, high impact to availability, and requires no user interaction. Atlassian recommends that Confluence Data Center and Server customers upgrade to latest version, if you are unable to do so, upgrade your instance to one of the specified supported fixed versions: Confluence Data Center and Server 7.19: Upgrade to a release greater than or equal to 7.19.14 Confluence Data Center and Server 8.5: Upgrade to a release greater than or equal to 8.5.1 Confluence Data Center and Server 8.6 or above: No need to upgrade, you're already on a patched version See the release notes (https://confluence.atlassian.com/doc/confluence-release-notes-327.html ). You can download the latest version of Confluence Data Center and Server from the download center (https://www.atlassian.com/software/confluence/download-archives ]). This vulnerability was reported via our Bug Bounty program.

**Neighbour 3**  |  dist 0.2829  |  HIGH  |  corpus-id CVE-2024-21672

> This High severity Remote Code Execution (RCE) vulnerability was introduced in version 2.1.0 of Confluence Data Center and Server.

Remote Code Execution (RCE) vulnerability, with a CVSS Score of 8.3 and a CVSS Vector of CVSS:3.0/AV:N/AC:H/PR:N/UI:R/S:C/C:H/I:H/A:H allows an unauthenticated attacker to remotely expose assets in your environment susceptible to exploitation which has high impact to confidentiality, high impact to integrity, high impact to availability, and requires user interaction.

Atlassian recommends that Confluence Data Center and Server customers upgrade to latest version, if you are unable to do so, upgrade your instance to one of the specified supported fixed versions:

* Confluence Data Center and Server 7.19: Upgrade to a release 7.19.18, or any higher 7.19.x release
* Confluence Data Center and Server 8.5: Upgrade to a release 8.5.5 or any higher 8.5.x release
* Confluence Data Center and Server 8.7: Upgrade to a release 8.7.2 or any higher release

See the release notes (https://confluence.atlassian.com/doc/confluence-release-notes-327.html ). You can download the latest version of Confluence Data Center and Server from the download center (https://www.atlassian.com/software/confluence/download-archives).

**Neighbour 4**  |  dist 0.3296  |  CRITICAL  |  corpus-id CVE-2023-22518

> All versions of Confluence Data Center and Server are affected by this unexploited vulnerability. This Improper Authorization vulnerability allows an unauthenticated attacker to reset Confluence and create a Confluence instance administrator account. Using this account, an attacker can then perform all administrative actions that are available to Confluence instance administrator leading to - but not limited to - full loss of confidentiality, integrity and availability. 

Atlassian Cloud sites are not affected by this vulnerability. If your Confluence site is accessed via an atlassian.net domain, it is hosted by Atlassian and is not vulnerable to this issue.

**Neighbour 5**  |  dist 0.3645  |  MEDIUM  |  corpus-id CVE-2020-29450

> Affected versions of Atlassian Confluence Server and Data Center allow remote attackers to impact the application's availability via a Denial of Service (DoS) vulnerability in the avatar upload feature. The affected versions are before version 7.2.0.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2024-3400  [CRITICAL, cell B, KEV=True, EPSS=0.99999]

**TARGET:** A command injection as a result of arbitrary file creation vulnerability in the GlobalProtect feature of Palo Alto Networks PAN-OS software for specific PAN-OS versions and distinct feature configurations may enable an unauthenticated attacker to execute arbitrary code with root privileges on the firewall.

Cloud NGFW, Panorama appliances, and Prisma Access are not impacted by this vulnerability.

nearest-neighbour distance: 0.2130  |  mean top-5 distance: 0.2554  |  max top-5 distance: 0.2725

**Neighbour 1**  |  dist 0.2130  |  MEDIUM  |  corpus-id CVE-2021-3045

> An OS command argument injection vulnerability in the Palo Alto Networks PAN-OS web interface enables an authenticated administrator to read any arbitrary file from the file system. This issue impacts: PAN-OS 8.1 versions earlier than PAN-OS 8.1.19; PAN-OS 9.0 versions earlier than PAN-OS 9.0.14; PAN-OS 9.1 versions earlier than PAN-OS 9.1.10. PAN-OS 10.0 and later versions are not impacted.

**Neighbour 2**  |  dist 0.2625  |  HIGH  |  corpus-id CVE-2025-0114

> A Denial of Service (DoS) vulnerability in the GlobalProtect feature of Palo Alto Networks PAN-OS software enables an unauthenticated attacker to render the service unavailable by sending a large number of specially crafted packets over a period of time. This issue affects both the GlobalProtect portal and the GlobalProtect gateway.

This issue does not apply to Cloud NGFWs or Prisma Access software.

**Neighbour 3**  |  dist 0.2643  |  MEDIUM  |  corpus-id CVE-2024-5913

> An improper input validation vulnerability in Palo Alto Networks PAN-OS software enables an attacker with the ability to tamper with the physical file system to elevate privileges.

**Neighbour 4**  |  dist 0.2647  |  MEDIUM  |  corpus-id CVE-2020-2039

> An uncontrolled resource consumption vulnerability in Palo Alto Networks PAN-OS allows for a remote unauthenticated user to upload temporary files through the management web interface that are not properly deleted after the request is finished. It is possible for an attacker to disrupt the availability of the management web interface by repeatedly uploading files until available disk space is exhausted. This issue impacts: PAN-OS 8.1 versions earlier than PAN-OS 8.1.16; PAN-OS 9.0 versions earlier than PAN-OS 9.0.10; PAN-OS 9.1 versions earlier than PAN-OS 9.1.4; PAN-OS 10.0 versions earlier than PAN-OS 10.0.1.

**Neighbour 5**  |  dist 0.2725  |  LOW  |  corpus-id CVE-2025-4614

> An information disclosure vulnerability in Palo Alto Networks PAN-OS® software enables an authenticated administrator to view session tokens of users authenticated to the firewall web UI. This may allow impersonation of users whose session tokens are leaked.  

The security risk posed by this issue is significantly minimized when CLI access is restricted to a limited group of administrators.

Cloud NGFW and Prisma® Access are not affected by this vulnerability.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-42013  [CRITICAL, cell B, KEV=True, EPSS=0.99964]

**TARGET:** It was found that the fix for CVE-2021-41773 in Apache HTTP Server 2.4.50 was insufficient. An attacker could use a path traversal attack to map URLs to files outside the directories configured by Alias-like directives. If files outside of these directories are not protected by the usual default configuration "require all denied", these requests can succeed. If CGI scripts are also enabled for these aliased pathes, this could allow for remote code execution. This issue only affects Apache 2.4.49 and Apache 2.4.50 and not earlier versions.

nearest-neighbour distance: 0.3897  |  mean top-5 distance: 0.4231  |  max top-5 distance: 0.4728

**Neighbour 1**  |  dist 0.3897  |  HIGH  |  corpus-id CVE-2026-44417

> The fix for CVE-2025-48913: Apache CXF: Untrusted JMS configuration can lead to RCE was not complete, meaning that another path in the code might lead to code execution capabilities, if untrusted users are allowed to configure JMS for Apache CXF. 
Users are recommended to upgrade to versions 4.2.1, 4.1.6 or 3.6.11, which fix this issue.

**Neighbour 2**  |  dist 0.3941  |  CRITICAL  |  corpus-id CVE-2024-38476

> Vulnerability in core of Apache HTTP Server 2.4.59 and earlier are vulnerably to information disclosure, SSRF or local script execution via backend applications whose response headers are malicious or exploitable.

Users are recommended to upgrade to version 2.4.60, which fixes this issue.

**Neighbour 3**  |  dist 0.4041  |  MEDIUM  |  corpus-id CVE-2024-39884

> A regression in the core of Apache HTTP Server 2.4.60 ignores some use of the legacy content-type based configuration of handlers.   "AddType" and similar configuration, under some circumstances where files are requested indirectly, result in source code disclosure of local content. For example, PHP scripts may be served instead of interpreted.

Users are recommended to upgrade to version 2.4.61, which fixes this issue.

**Neighbour 4**  |  dist 0.4545  |  HIGH  |  corpus-id CVE-2023-32679

> Craft CMS is an open source content management system. In affected versions of Craft CMS an unrestricted file extension may lead to Remote Code Execution. If the name parameter value is not empty string('') in the View.php's doesTemplateExist() -> resolveTemplate() -> _resolveTemplateInternal() -> _resolveTemplate() function, it returns directly without extension verification, so that arbitrary extension files are rendered as twig templates. When attacker with admin privileges on a DEV or an improperly configured STG or PROD environment, they can exploit this vulnerability to remote code execution. Code execution may grant the attacker access to the host operating system. This issue has been addressed in version 4.4.6. Users are advised to upgrade. There are no known workarounds for this vulnerability.

**Neighbour 5**  |  dist 0.4728  |  MEDIUM  |  corpus-id CVE-2022-24969

> bypass CVE-2021-25640 > In Apache Dubbo prior to 2.6.12 and 2.7.15, the usage of parseURL method will lead to the bypass of the white host check which can cause open redirect or SSRF vulnerability.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2020-8958  [HIGH, cell C, KEV=False, EPSS=0.46642]

**TARGET:** Guangzhou 1GE ONU V2801RW 1.9.1-181203 through 2.9.0-181024 and V2804RGW 1.9.1-181203 through 2.9.0-181024 devices allow remote attackers to execute arbitrary OS commands via shell metacharacters in the boaform/admin/formPing Dest IP Address field.

nearest-neighbour distance: 0.4206  |  mean top-5 distance: 0.4825  |  max top-5 distance: 0.5083

**Neighbour 1**  |  dist 0.4206  |  CRITICAL  |  corpus-id CVE-2021-30234

> The api/ZRIGMP/set_MLD_PROXY interface in China Mobile An Lianbao WF-1 router 1.0.1 allows remote attackers to execute arbitrary commands via shell metacharacters in the MLD_PROXY_WAN_CONNECT parameter.

**Neighbour 2**  |  dist 0.4774  |  HIGH  |  corpus-id CVE-2022-45045

> Multiple Xiongmai NVR devices, including MBD6304T V4.02.R11.00000117.10001.131900.00000 and NBD6808T-PL V4.02.R11.C7431119.12001.130000.00000, allow authenticated users to execute arbitrary commands as root, as exploited in the wild starting in approximately 2019. A remote and authenticated attacker, possibly using the default admin:tlJwpbo6 credentials, can connect to port 34567 and execute arbitrary operating system commands via a crafted JSON file during an upgrade request. Since at least 2021, Xiongmai has applied patches to prevent attackers from using this mechanism to execute telnetd.

**Neighbour 3**  |  dist 0.5005  |  MEDIUM  |  corpus-id CVE-2021-20804

> Cybozu Remote Service 3.1.8 to 3.1.9 allows a remote authenticated attacker to cause a denial of service (DoS) condition via unspecified vectors.

**Neighbour 4**  |  dist 0.5059  |  HIGH  |  corpus-id CVE-2021-20708

> NEC Aterm devices (Aterm WF1200CR firmware Ver1.3.2 and earlier, Aterm WG1200CR firmware Ver1.3.3 and earlier, and Aterm WG2600HS firmware Ver1.5.1 and earlier) allow authenticated attackers to execute arbitrary OS commands by sending a specially crafted request to a specific URL.

**Neighbour 5**  |  dist 0.5083  |  CRITICAL  |  corpus-id CVE-2022-30525

> A OS command injection vulnerability in the CGI program of Zyxel USG FLEX 100(W) firmware versions 5.00 through 5.21 Patch 1, USG FLEX 200 firmware versions 5.00 through 5.21 Patch 1, USG FLEX 500 firmware versions 5.00 through 5.21 Patch 1, USG FLEX 700 firmware versions 5.00 through 5.21 Patch 1, USG FLEX 50(W) firmware versions 5.10 through 5.21 Patch 1, USG20(W)-VPN firmware versions 5.10 through 5.21 Patch 1, ATP series firmware versions 5.10 through 5.21 Patch 1, VPN series firmware versions 4.60 through 5.21 Patch 1, which could allow an attacker to modify specific files and then execute some OS commands on a vulnerable device.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-43661  [HIGH, cell C, KEV=False, EPSS=0.46904]

**TARGET:** Cachet, the open-source status page system. Prior to the 2.4 branch, a template functionality which allows users to create templates allows them to execute any code on the server during the bad filtration and old twig version. Commit 6fb043e109d2a262ce3974e863c54e9e5f5e0587 of the 2.4 branch contains a patch for this issue.

nearest-neighbour distance: 0.5411  |  mean top-5 distance: 0.5552  |  max top-5 distance: 0.5651

**Neighbour 1**  |  dist 0.5411  |  CRITICAL  |  corpus-id CVE-2024-38476

> Vulnerability in core of Apache HTTP Server 2.4.59 and earlier are vulnerably to information disclosure, SSRF or local script execution via backend applications whose response headers are malicious or exploitable.

Users are recommended to upgrade to version 2.4.60, which fixes this issue.

**Neighbour 2**  |  dist 0.5515  |  MEDIUM  |  corpus-id CVE-2022-49828

> In the Linux kernel, the following vulnerability has been resolved:

hugetlbfs: don't delete error page from pagecache

This change is very similar to the change that was made for shmem [1], and
it solves the same problem but for HugeTLBFS instead.

Currently, when poison is found in a HugeTLB page, the page is removed
from the page cache.  That means that attempting to map or read that
hugepage in the future will result in a new hugepage being allocated
instead of notifying the user that the page was poisoned.  As [1] states,
this is effectively memory corruption.

The fix is to leave the page in the page cache.  If the user attempts to
use a poisoned HugeTLB page with a syscall, the syscall will fail with
EIO, the same error code that shmem uses.  For attempts to map the page,
the thread will get a BUS_MCEERR_AR SIGBUS.

[1]: commit a76054266661 ("mm: shmem: don't truncate page if memory failure happens")

**Neighbour 3**  |  dist 0.5552  |  MEDIUM  |  corpus-id CVE-2024-39884

> A regression in the core of Apache HTTP Server 2.4.60 ignores some use of the legacy content-type based configuration of handlers.   "AddType" and similar configuration, under some circumstances where files are requested indirectly, result in source code disclosure of local content. For example, PHP scripts may be served instead of interpreted.

Users are recommended to upgrade to version 2.4.61, which fixes this issue.

**Neighbour 4**  |  dist 0.5630  |  MEDIUM  |  corpus-id CVE-2024-5005

> An issue has been discovered discovered in GitLab EE/CE affecting all versions starting from 11.4 before 17.2.9, all versions starting from 17.3 before 17.3.5, all versions starting from 17.4 before 17.4.2 It was possible for guest users to disclose project templates using the API.

**Neighbour 5**  |  dist 0.5651  |  HIGH  |  corpus-id CVE-2023-32679

> Craft CMS is an open source content management system. In affected versions of Craft CMS an unrestricted file extension may lead to Remote Code Execution. If the name parameter value is not empty string('') in the View.php's doesTemplateExist() -> resolveTemplate() -> _resolveTemplateInternal() -> _resolveTemplate() function, it returns directly without extension verification, so that arbitrary extension files are rendered as twig templates. When attacker with admin privileges on a DEV or an improperly configured STG or PROD environment, they can exploit this vulnerability to remote code execution. Code execution may grant the attacker access to the host operating system. This issue has been addressed in version 4.4.6. Users are advised to upgrade. There are no known workarounds for this vulnerability.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-21974  [HIGH, cell C, KEV=False, EPSS=0.45063]

**TARGET:** OpenSLP as used in ESXi (7.0 before ESXi70U1c-17325551, 6.7 before ESXi670-202102401-SG, 6.5 before ESXi650-202102101-SG) has a heap-overflow vulnerability. A malicious actor residing within the same network segment as ESXi who has access to port 427 may be able to trigger the heap-overflow issue in OpenSLP service resulting in remote code execution.

nearest-neighbour distance: 0.3521  |  mean top-5 distance: 0.4412  |  max top-5 distance: 0.4730

**Neighbour 1**  |  dist 0.3521  |  MEDIUM  |  corpus-id CVE-2020-3971

> VMware ESXi (6.7 before ESXi670-201904101-SG and 6.5 before ESXi650-201907101-SG), Workstation (15.x before 15.0.2), and Fusion (11.x before 11.0.2) contain a heap overflow vulnerability in the vmxnet3 virtual network adapter. A malicious actor with local access to a virtual machine with a vmxnet3 network adapter present may be able to read privileged information contained in physical memory.

**Neighbour 2**  |  dist 0.4564  |  MEDIUM  |  corpus-id CVE-2026-8121

> A vulnerability has been found in Open5GS up to 2.7.7. The impacted element is the function ogs_sbi_parse_plmn_list in the library /lib/sbi/conv.c of the component NSSF. The manipulation leads to denial of service. The attack is possible to be carried out remotely. The exploit has been disclosed to the public and may be used. The project was informed of the problem early through an issue report but has not responded yet.

**Neighbour 3**  |  dist 0.4607  |  HIGH  |  corpus-id CVE-2020-12861

> A heap buffer overflow in SANE Backends before 1.0.30 allows a malicious device connected to the same local network as the victim to execute arbitrary code, aka GHSL-2020-080.

**Neighbour 4**  |  dist 0.4635  |  HIGH  |  corpus-id CVE-2021-25479

> A possible heap-based buffer overflow vulnerability in Exynos CP Chipset prior to SMR Oct-2021 Release 1 allows arbitrary memory write and code execution.

**Neighbour 5**  |  dist 0.4730  |  CRITICAL  |  corpus-id CVE-2022-2329

> A CWE-190: Integer Overflow or Wraparound vulnerability exists that could cause heap-based buffer overflow, leading to denial of service and potentially remote code execution when an attacker sends multiple specially crafted messages. Affected Products: IGSS Data Server - IGSSdataServer.exe (Versions prior to V15.0.0.22073)

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-22717  [HIGH, cell C, KEV=False, EPSS=0.38912]

**TARGET:** A CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal') vulnerability exists in C-Bus Toolkit (V1.15.7 and prior) that could allow a remote code execution when processing config files.

nearest-neighbour distance: 0.3380  |  mean top-5 distance: 0.3808  |  max top-5 distance: 0.4016

**Neighbour 1**  |  dist 0.3380  |  HIGH  |  corpus-id CVE-2022-23447

> An improper limitation of a pathname to a restricted directory ('Path Traversal') vulnerability [CWE-22] in FortiExtender management interface  7.0.0 through 7.0.3, 4.2.0 through 4.2.4, 4.1.1 through 4.1.8, 4.0.0 through 4.0.2, 3.3.0 through 3.3.2, 3.2.1 through 3.2.3, 5.3 all versions may allow an unauthenticated and remote attacker to retrieve arbitrary files from the underlying filesystem via specially crafted web requests.

**Neighbour 2**  |  dist 0.3730  |  HIGH  |  corpus-id CVE-2025-62630

> Due to insufficient sanitization, an attacker can upload a specially 
crafted configuration file to traverse directories and achieve remote 
code execution with system-level permissions.

**Neighbour 3**  |  dist 0.3933  |  CRITICAL  |  corpus-id CVE-2024-3322

> A path traversal vulnerability exists in the 'cyber_security/codeguard' native personality of the parisneo/lollms-webui, affecting versions up to 9.5. The vulnerability arises from the improper limitation of a pathname to a restricted directory in the 'process_folder' function within 'lollms-webui/zoos/personalities_zoo/cyber_security/codeguard/scripts/processor.py'. Specifically, the function fails to properly sanitize user-supplied input for the 'code_folder_path', allowing an attacker to specify arbitrary paths using '../' or absolute paths. This flaw leads to arbitrary file read and overwrite capabilities in specified directories without limitations, posing a significant risk of sensitive information disclosure and unauthorized file manipulation.

**Neighbour 4**  |  dist 0.3979  |  HIGH  |  corpus-id CVE-2025-52452

> Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal') vulnerability in Salesforce Tableau Server on Windows, Linux (tabdoc api - duplicate-data-source modules) allows Absolute Path Traversal. This issue affects Tableau Server: before 2025.1.3, before 2024.2.12, before 2023.3.19.

**Neighbour 5**  |  dist 0.4016  |  HIGH  |  corpus-id CVE-2025-48817

> Relative path traversal in Remote Desktop Client allows an unauthorized attacker to execute code over a network.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2020-8260  [HIGH, cell D, KEV=True, EPSS=0.9648]

**TARGET:** A vulnerability in the Pulse Connect Secure < 9.1R9 admin web interface could allow an authenticated attacker to perform an arbitrary code execution using uncontrolled gzip extraction.

nearest-neighbour distance: 0.1742  |  mean top-5 distance: 0.3611  |  max top-5 distance: 0.4397

**Neighbour 1**  |  dist 0.1742  |  HIGH  |  corpus-id CVE-2020-8218

> A code injection vulnerability exists in Pulse Connect Secure <9.1R8 that allows an attacker to crafted a URI to perform an arbitrary code execution via the admin web interface.

**Neighbour 2**  |  dist 0.3154  |  MEDIUM  |  corpus-id CVE-2020-8220

> A denial of service vulnerability exists in Pulse Connect Secure <9.1R8 that allows an authenticated attacker to perform command injection via the administrator web which can cause DOS.

**Neighbour 3**  |  dist 0.4370  |  HIGH  |  corpus-id CVE-2024-23967

> Autel MaxiCharger AC Elite Business C50 WebSocket Base64 Decoding Stack-based Buffer Overflow Remote Code Execution Vulnerability. This vulnerability allows network-adjacent attackers to execute arbitrary code on affected installations of Autel MaxiCharger AC Elite Business C50 chargers. Although authentication is required to exploit this vulnerability, the existing authentication mechanism can be bypassed.

The specific flaw exists within the handling of base64-encoded data within WebSocket messages. The issue results from the lack of proper validation of the length of user-supplied data prior to copying it to a fixed-length stack-based buffer. An attacker can leverage this vulnerability to execute code in the context of the device.

Was ZDI-CAN-23230

**Neighbour 4**  |  dist 0.4390  |  CRITICAL  |  corpus-id CVE-2020-17407

> This vulnerability allows remote attackers to execute arbitrary code on affected installations of Microhard Bullet-LTE prior to v1.2.0-r1112. Authentication is not required to exploit this vulnerability. The specific flaw exists within the handling of authentication headers. The issue results from the lack of proper validation of the length of user-supplied data prior to copying it to a fixed-length stack-based buffer. An attacker can leverage this vulnerability to execute code in the context of root. Was ZDI-CAN-10596.

**Neighbour 5**  |  dist 0.4397  |  HIGH  |  corpus-id CVE-2022-43971

> An arbitrary code exection vulnerability exists in Linksys WUMC710 Wireless-AC Universal Media Connector with firmware <= 1.0.02 (build3). The do_setNTP function within the httpd binary uses unvalidated user input in the construction of a system command. An authenticated attacker with administrator privileges can leverage this vulnerability over the network via a malicious GET or POST request to /setNTP.cgi to execute arbitrary commands on the underlying Linux operating system as root.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-44221  [HIGH, cell D, KEV=True, EPSS=0.74933]

**TARGET:** Improper neutralization of special elements in the SMA100 SSL-VPN management interface allows a remote authenticated attacker with administrative privilege to inject arbitrary commands as a 'nobody' user, potentially leading to OS Command Injection Vulnerability.

nearest-neighbour distance: 0.3136  |  mean top-5 distance: 0.3825  |  max top-5 distance: 0.4141

**Neighbour 1**  |  dist 0.3136  |  HIGH  |  corpus-id CVE-2025-32820

> A vulnerability in SMA100 allows a remote authenticated attacker with SSLVPN user privileges can inject a path traversal sequence to make any directory on the SMA appliance writable.

**Neighbour 2**  |  dist 0.3874  |  HIGH  |  corpus-id CVE-2026-20103

> A vulnerability in the Remote Access SSL VPN functionality of Cisco Secure Firewall Adaptive Security Appliance (ASA) Software and Secure Firewall Threat Defense (FTD) Software could allow an unauthenticated, remote attacker to exhaust device memory resulting in a denial of service (DoS) condition to new Remote Access SSL VPN connections. This does not affect the management interface, though it may become temporarily unresponsive. 
 This vulnerability is due to trusting user input without validation. An attacker could exploit this vulnerability by sending crafted packets to the Remote Access SSL VPN server. A successful exploit could allow the attacker to cause the device web interface to stop responding, resulting in a DoS condition.

**Neighbour 3**  |  dist 0.3889  |  CRITICAL  |  corpus-id CVE-2021-43928

> Improper neutralization of special elements used in an OS command ('OS Command Injection') vulnerability in mail sending and receiving component in Synology Mail Station before 20211105-10315 allows remote authenticated users to execute arbitrary commands via unspecified vectors.

**Neighbour 4**  |  dist 0.4083  |  CRITICAL  |  corpus-id CVE-2026-6644

> A command injection vulnerability was found in the PPTP VPN Clients on the ADM. The vulnerability allows an administrative user to break out of the restricted web environment and execute arbitrary code on the underlying operating system. This occurs due to insufficient validation of user-supplied input before it is passed to a system shell. Successful exploitation allows an attacker to achieve Remote Code Execution (RCE) and fully compromise the system.
Affected products and versions include: from ADM 4.1.0 through ADM 4.3.3.RR42 as well as from ADM 5.0.0 through ADM 5.1.2.REO1.

**Neighbour 5**  |  dist 0.4141  |  MEDIUM  |  corpus-id CVE-2023-20247

> A vulnerability in the remote access SSL VPN feature of Cisco Adaptive Security Appliance (ASA) Software and Cisco Firepower Threat Defense (FTD) Software could allow an authenticated, remote attacker to bypass a configured multiple certificate authentication policy and connect using only a valid username and password. This vulnerability is due to improper error handling during remote access VPN authentication. An attacker could exploit this vulnerability by sending crafted requests during remote access VPN session establishment. A successful exploit could allow the attacker to bypass the configured multiple certificate authentication policy while retaining the privileges and permissions associated with the original connection profile.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2020-8655  [HIGH, cell D, KEV=True, EPSS=0.57258]

**TARGET:** An issue was discovered in EyesOfNetwork 5.3. The sudoers configuration is prone to a privilege escalation vulnerability, allowing the apache user to run arbitrary commands as root via a crafted NSE script for nmap 7.

nearest-neighbour distance: 0.5283  |  mean top-5 distance: 0.5420  |  max top-5 distance: 0.5533

**Neighbour 1**  |  dist 0.5283  |  CRITICAL  |  corpus-id CVE-2020-11920

> An issue was discovered in Svakom Siime Eye 14.1.00000001.3.330.0.0.3.14. A command injection vulnerability resides in the HOST/IP section of the NFS settings menu in the webserver running on the device. By injecting Bash commands via shell metacharacters here, the device executes arbitrary code with root privileges (all of the device's services are running as root).

**Neighbour 2**  |  dist 0.5424  |  MEDIUM  |  corpus-id CVE-2024-39347

> Incorrect default permissions vulnerability in firewall functionality in Synology Router Manager (SRM) before 1.2.5-8227-11 and 1.3.1-9346-8 allows man-in-the-middle attackers to access highly sensitive intranet resources via unspecified vectors.

**Neighbour 3**  |  dist 0.5425  |  HIGH  |  corpus-id CVE-2020-27872

> This vulnerability allows network-adjacent attackers to bypass authentication on affected installations of NETGEAR R7450 1.2.0.62_1.0.1 routers. Authentication is not required to exploit this vulnerability. The specific flaw exists within the mini_httpd service, which listens on TCP port 80 by default. The issue results from improper state tracking in the password recovery process. An attacker can leverage this in conjunction with other vulnerabilities to execute code in the context of root. Was ZDI-CAN-11365.

**Neighbour 4**  |  dist 0.5434  |  HIGH  |  corpus-id CVE-2021-34979

> This vulnerability allows network-adjacent attackers to execute arbitrary code on affected installations of NETGEAR R6260 1.1.0.78_1.0.1 routers. Authentication is not required to exploit this vulnerability. The specific flaw exists within the handling of SOAP requests. When parsing the SOAPAction header, the process does not properly validate the length of user-supplied data prior to copying it to a fixed-length buffer. An attacker can leverage this vulnerability to execute code in the context of root. Was ZDI-CAN-13512.

**Neighbour 5**  |  dist 0.5533  |  HIGH  |  corpus-id CVE-2024-29228

> Missing authorization vulnerability in GetStmUrlPath webapi component in Synology Surveillance Station before 9.2.0-9289 and 9.2.0-11289 allows remote authenticated users to obtain sensitive information via unspecified vectors.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-21608  [HIGH, cell D, KEV=True, EPSS=0.61475]

**TARGET:** Adobe Acrobat Reader versions 22.003.20282 (and earlier), 22.003.20281 (and earlier) and 20.005.30418 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

nearest-neighbour distance: 0.0068  |  mean top-5 distance: 0.0096  |  max top-5 distance: 0.0118

**Neighbour 1**  |  dist 0.0068  |  HIGH  |  corpus-id CVE-2022-34216

> Adobe Acrobat Reader versions 22.001.20142 (and earlier), 20.005.30334 (and earlier) and 17.012.30229 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

**Neighbour 2**  |  dist 0.0068  |  HIGH  |  corpus-id CVE-2022-34230

> Adobe Acrobat Reader versions 22.001.20142 (and earlier), 20.005.30334 (and earlier) and 17.012.30229 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

**Neighbour 3**  |  dist 0.0111  |  HIGH  |  corpus-id CVE-2023-26420

> Adobe Acrobat Reader versions 23.001.20093 (and earlier) and 20.005.30441 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

**Neighbour 4**  |  dist 0.0118  |  HIGH  |  corpus-id CVE-2023-44336

> Adobe Acrobat Reader versions 23.006.20360 (and earlier) and 20.005.30524 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

**Neighbour 5**  |  dist 0.0118  |  HIGH  |  corpus-id CVE-2023-44372

> Adobe Acrobat Reader versions 23.006.20360 (and earlier) and 20.005.30524 (and earlier) are affected by a Use After Free vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2022-3062  [MEDIUM, cell E, KEV=False, EPSS=0.37405]

**TARGET:** The Simple File List WordPress plugin before 4.4.12 does not escape parameters before outputting them back in attributes, leading to Reflected Cross-Site Scripting

nearest-neighbour distance: 0.3628  |  mean top-5 distance: 0.3836  |  max top-5 distance: 0.4050

**Neighbour 1**  |  dist 0.3628  |  MEDIUM  |  corpus-id CVE-2021-24961

> The WordPress File Upload WordPress plugin before 4.16.3, wordpress-file-upload-pro WordPress plugin before 4.16.3 does not escape some of its shortcode argument, which could allow users with a role as low as Contributor to perform Cross-Site Scripting attacks

**Neighbour 2**  |  dist 0.3748  |  MEDIUM  |  corpus-id CVE-2022-1220

> The FoxyShop WordPress plugin before 4.8.2 does not sanitise and escape a parameter before outputting it back in an admin page, leading to a Reflected Cross-Site Scripting

**Neighbour 3**  |  dist 0.3839  |  MEDIUM  |  corpus-id CVE-2022-2654

> The Classima WordPress theme before 2.1.11 and some of its required plugins (Classified Listing before 2.2.14, Classified Listing Pro before 2.0.20, Classified Listing Store & Membership before 1.4.20 and Classima Core before 1.10) do not escape a parameter before outputting it back in attributes, leading to Reflected Cross-Site Scripting

**Neighbour 4**  |  dist 0.3914  |  MEDIUM  |  corpus-id CVE-2022-0503

> The WordPress Multisite Content Copier/Updater WordPress plugin before 2.1.2 does not sanitise and escape the s parameter before outputting it back in an attribute, leading to a Reflected Cross-Site Scripting issue in the network dashboard

**Neighbour 5**  |  dist 0.4050  |  MEDIUM  |  corpus-id CVE-2022-0201

> The Permalink Manager Lite WordPress plugin before 2.2.15 and Permalink Manager Pro WordPress plugin before 2.2.15 do not sanitise and escape query parameters before outputting them back in the debug page, leading to a Reflected Cross-Site Scripting issue

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2023-0157  [MEDIUM, cell E, KEV=False, EPSS=0.32462]

**TARGET:** The All-In-One Security (AIOS) WordPress plugin before 5.1.5 does not escape the content of log files before outputting it to the plugin admin page, allowing an authorized user (admin+) to plant bogus log files containing malicious JavaScript code that will be executed in the context of any administrator visiting this page.

nearest-neighbour distance: 0.3457  |  mean top-5 distance: 0.3816  |  max top-5 distance: 0.4037

**Neighbour 1**  |  dist 0.3457  |  MEDIUM  |  corpus-id CVE-2024-1037

> The All-In-One Security (AIOS) – Security and Firewall plugin for WordPress is vulnerable to Reflected Cross-Site Scripting via the 'tab' parameter in all versions up to, and including, 5.2.5 due to insufficient input sanitization and output escaping. This makes it possible for unauthenticated attackers to inject arbitrary web scripts in pages that execute if they can successfully trick a user into performing an action such as clicking on a link.

**Neighbour 2**  |  dist 0.3629  |  MEDIUM  |  corpus-id CVE-2024-3921

> The Gianism WordPress plugin through 5.1.0 does not sanitise and escape some of its settings, which could allow high privilege users such as admin to perform Stored Cross-Site Scripting attacks even when the unfiltered_html capability is disallowed (for example in multisite setup)

**Neighbour 3**  |  dist 0.3944  |  MEDIUM  |  corpus-id CVE-2023-2742

> The AI ChatBot WordPress plugin before 4.5.5 does not sanitize and escape its settings, allowing high-privilege users such as admin to perform Cross-Site Scripting attacks even when the unfiltered_html capability is disallowed.

**Neighbour 4**  |  dist 0.4012  |  MEDIUM  |  corpus-id CVE-2024-6669

> The AI ChatBot for WordPress – WPBot plugin for WordPress is vulnerable to Stored Cross-Site Scripting via admin settings in all versions up to, and including, 5.5.7 due to insufficient input sanitization and output escaping. This makes it possible for authenticated attackers, with administrator-level permissions and above, to inject arbitrary web scripts in pages that will execute whenever a user accesses an injected page. This only affects multi-site installations and installations where unfiltered_html has been disabled.

**Neighbour 5**  |  dist 0.4037  |  MEDIUM  |  corpus-id CVE-2023-5772

> The Debug Log Manager plugin for WordPress is vulnerable to Cross-Site Request Forgery in all versions up to, and including, 2.2.1. This is due to missing or incorrect nonce validation on the clear_log() function. This makes it possible for unauthenticated attackers to clear the debug log via a forged request granted they can trick a site administrator into performing an action such as clicking on a link.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-30970  [MEDIUM, cell E, KEV=False, EPSS=0.13453]

**TARGET:** A logic issue was addressed with improved state management. This issue is fixed in macOS Monterey 12.1, macOS Big Sur 11.6.2. A malicious application may be able to bypass Privacy preferences.

nearest-neighbour distance: 0.1506  |  mean top-5 distance: 0.1914  |  max top-5 distance: 0.2430

**Neighbour 1**  |  dist 0.1506  |  MEDIUM  |  corpus-id CVE-2021-30965

> A logic issue was addressed with improved state management. This issue is fixed in macOS Monterey 12.1, Security Update 2021-008 Catalina, macOS Big Sur 11.6.2. A malicious application may be able to cause a denial of service to Endpoint Security clients.

**Neighbour 2**  |  dist 0.1674  |  MEDIUM  |  corpus-id CVE-2022-26746

> This issue was addressed by removing the vulnerable code. This issue is fixed in Security Update 2022-004 Catalina, macOS Monterey 12.4, macOS Big Sur 11.6.6. A malicious application may be able to bypass Privacy preferences.

**Neighbour 3**  |  dist 0.1879  |  CRITICAL  |  corpus-id CVE-2021-30678

> A logic issue was addressed with improved state management. This issue is fixed in macOS Big Sur 11.4, Security Update 2021-003 Catalina, Security Update 2021-004 Mojave. A remote attacker may be able to cause unexpected application termination or arbitrary code execution.

**Neighbour 4**  |  dist 0.2081  |  MEDIUM  |  corpus-id CVE-2021-30990

> A logic issue was addressed with improved validation. This issue is fixed in macOS Monterey 12.1, Security Update 2021-008 Catalina, macOS Big Sur 11.6.2. A malicious application may bypass Gatekeeper checks.

**Neighbour 5**  |  dist 0.2430  |  CRITICAL  |  corpus-id CVE-2022-26776

> This issue was addressed with improved checks. This issue is fixed in macOS Monterey 12.4, macOS Big Sur 11.6.6. An attacker may be able to cause unexpected application termination or arbitrary code execution.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2024-1781  [MEDIUM, cell E, KEV=False, EPSS=0.14692]

**TARGET:** A vulnerability was found in Totolink X6000R AX3000 9.4.0cu.852_20230719. It has been rated as critical. This issue affects the function setWizardCfg of the file /cgi-bin/cstecgi.cgi of the component shttpd. The manipulation leads to command injection. The exploit has been disclosed to the public and may be used. The identifier VDB-254573 was assigned to this vulnerability. NOTE: The vendor was contacted early about this disclosure but did not respond in any way.

nearest-neighbour distance: 0.1880  |  mean top-5 distance: 0.1969  |  max top-5 distance: 0.2040

**Neighbour 1**  |  dist 0.1880  |  HIGH  |  corpus-id CVE-2024-7185

> A vulnerability was found in TOTOLINK A3600R 4.1.2cu.5182_B20201102 and classified as critical. Affected by this issue is the function setWebWlanIdx of the file /cgi-bin/cstecgi.cgi. The manipulation of the argument webWlanIdx leads to buffer overflow. The attack may be launched remotely. The exploit has been disclosed to the public and may be used. VDB-272606 is the identifier assigned to this vulnerability. NOTE: The vendor was contacted early about this disclosure but did not respond in any way.

**Neighbour 2**  |  dist 0.1880  |  MEDIUM  |  corpus-id CVE-2025-3665

> A vulnerability has been found in TOTOLINK A3700R 9.1.2u.5822_B20200513 and classified as critical. Affected by this vulnerability is the function setSmartQosCfg of the file /cgi-bin/cstecgi.cgi. The manipulation leads to improper access controls. The attack can be launched remotely. The exploit has been disclosed to the public and may be used. The vendor was contacted early about this disclosure but did not respond in any way.

**Neighbour 3**  |  dist 0.2006  |  MEDIUM  |  corpus-id CVE-2025-9934

> A vulnerability was found in TOTOLINK X5000R 9.1.0cu.2415_B20250515. This affects the function sub_410C34 of the file /cgi-bin/cstecgi.cgi. Performing manipulation of the argument pid results in command injection. Remote exploitation of the attack is possible. The exploit has been made public and could be used.

**Neighbour 4**  |  dist 0.2038  |  MEDIUM  |  corpus-id CVE-2025-3663

> A vulnerability, which was classified as critical, has been found in TOTOLINK A3700R 9.1.2u.5822_B20200513. This issue affects the function setWiFiEasyCfg/setWiFiEasyGuestCfg of the file /cgi-bin/cstecgi.cgi of the component Password Handler. The manipulation leads to improper access controls. The attack may be initiated remotely. The exploit has been disclosed to the public and may be used. The vendor was contacted early about this disclosure but did not respond in any way.

**Neighbour 5**  |  dist 0.2040  |  MEDIUM  |  corpus-id CVE-2025-4850

> A vulnerability classified as critical has been found in TOTOLINK N300RH 6.1c.1390_B20191101. This affects the function setUnloadUserData of the file /cgi-bin/cstecgi.cgi. The manipulation of the argument plugin_name leads to command injection. It is possible to initiate the attack remotely. The exploit has been disclosed to the public and may be used.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-37976  [MEDIUM, cell F, KEV=True, EPSS=0.19901]

**TARGET:** Inappropriate implementation in Memory in Google Chrome prior to 94.0.4606.71 allowed a remote attacker to obtain potentially sensitive information from process memory via a crafted HTML page.

nearest-neighbour distance: 0.1309  |  mean top-5 distance: 0.1440  |  max top-5 distance: 0.1632

**Neighbour 1**  |  dist 0.1309  |  HIGH  |  corpus-id CVE-2021-21225

> Out of bounds memory access in V8 in Google Chrome prior to 90.0.4430.85 allowed a remote attacker to potentially exploit heap corruption via a crafted HTML page.

**Neighbour 2**  |  dist 0.1310  |  HIGH  |  corpus-id CVE-2024-6101

> Inappropriate implementation in V8 in Google Chrome prior to 126.0.6478.114 allowed a remote attacker to perform out of bounds memory access via a crafted HTML page. (Chromium security severity: High)

**Neighbour 3**  |  dist 0.1341  |  MEDIUM  |  corpus-id CVE-2026-10994

> Uninitialized Use in ANGLE in Google Chrome prior to 149.0.7827.53 allowed a remote attacker to obtain potentially sensitive information from process memory via a crafted HTML page. (Chromium security severity: Medium)

**Neighbour 4**  |  dist 0.1609  |  HIGH  |  corpus-id CVE-2020-16009

> Inappropriate implementation in V8 in Google Chrome prior to 86.0.4240.183 allowed a remote attacker to potentially exploit heap corruption via a crafted HTML page.

**Neighbour 5**  |  dist 0.1632  |  HIGH  |  corpus-id CVE-2020-15979

> Inappropriate implementation in V8 in Google Chrome prior to 86.0.4240.75 allowed a remote attacker to potentially exploit heap corruption via a crafted HTML page.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2022-28810  [MEDIUM, cell F, KEV=True, EPSS=0.70419]

**TARGET:** Zoho ManageEngine ADSelfService Plus before build 6122 allows a remote authenticated administrator to execute arbitrary operating OS commands as SYSTEM via the policy custom script feature. Due to the use of a default administrator password, attackers may be able to abuse this functionality with minimal effort. Additionally, a remote and partially authenticated attacker may be able to inject arbitrary commands into the custom script due to an unsanitized password field.

nearest-neighbour distance: 0.2915  |  mean top-5 distance: 0.3568  |  max top-5 distance: 0.3872

**Neighbour 1**  |  dist 0.2915  |  CRITICAL  |  corpus-id CVE-2023-35854

> Zoho ManageEngine ADSelfService Plus through 6113 has an authentication bypass that can be exploited to steal the domain controller session token for identity spoofing, thereby achieving the privileges of the domain controller administrator. NOTE: the vendor's perspective is that they have "found no evidence or detail of a security vulnerability."

**Neighbour 2**  |  dist 0.3683  |  CRITICAL  |  corpus-id CVE-2021-37918

> Zoho ManageEngine ADManager Plus version 7110 and prior allows unrestricted file upload which leads to remote code execution.

**Neighbour 3**  |  dist 0.3683  |  CRITICAL  |  corpus-id CVE-2021-37924

> Zoho ManageEngine ADManager Plus version 7110 and prior allows unrestricted file upload which leads to remote code execution.

**Neighbour 4**  |  dist 0.3687  |  HIGH  |  corpus-id CVE-2020-35682

> Zoho ManageEngine ServiceDesk Plus before 11134 allows an Authentication Bypass (only during SAML login).

**Neighbour 5**  |  dist 0.3872  |  CRITICAL  |  corpus-id CVE-2021-42002

> Zoho ManageEngine ADManager Plus before 7115 is vulnerable to a filter bypass that leads to file-upload remote code execution.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2021-22204  [MEDIUM, cell F, KEV=True, EPSS=0.99981]

**TARGET:** Improper neutralization of user data in the DjVu file format in ExifTool versions 7.44 and up allows arbitrary code execution when parsing the malicious image

nearest-neighbour distance: 0.3898  |  mean top-5 distance: 0.4533  |  max top-5 distance: 0.4795

**Neighbour 1**  |  dist 0.3898  |  MEDIUM  |  corpus-id CVE-2023-47996

> An integer overflow vulnerability in Exif.cpp::jpeg_read_exif_dir in FreeImage 3.18.0 allows attackers to obtain information and cause a denial of service.

**Neighbour 2**  |  dist 0.4600  |  MEDIUM  |  corpus-id CVE-2021-3482

> A flaw was found in Exiv2 in versions before and including 0.27.4-RC1. Improper input validation of the rawData.size property in Jp2Image::readMetadata() in jp2image.cpp can lead to a heap-based buffer overflow via a crafted JPG image containing malicious EXIF data.

**Neighbour 3**  |  dist 0.4667  |  HIGH  |  corpus-id CVE-2020-21483

> An arbitrary file upload vulnerability in Jizhicms v1.5 allows attackers to execute arbitrary code via a crafted .jpg file which is later changed to a PHP file.

**Neighbour 4**  |  dist 0.4705  |  CRITICAL  |  corpus-id CVE-2022-48008

> An arbitrary file upload vulnerability in the plugin manager of LimeSurvey v5.4.15 allows attackers to execute arbitrary code via a crafted PHP file.

**Neighbour 5**  |  dist 0.4795  |  HIGH  |  corpus-id CVE-2024-49551

> Media Encoder versions 25.0, 24.6.3 and earlier are affected by an out-of-bounds write vulnerability that could result in arbitrary code execution in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

### CVE-2022-40765  [MEDIUM, cell F, KEV=True, EPSS=0.10481]

**TARGET:** A vulnerability in the Edge Gateway component of Mitel MiVoice Connect through 19.3 (22.22.6100.0) could allow an authenticated attacker with internal network access to conduct a command-injection attack, due to insufficient restriction of URL parameters.

nearest-neighbour distance: 0.4328  |  mean top-5 distance: 0.4562  |  max top-5 distance: 0.4728

**Neighbour 1**  |  dist 0.4328  |  HIGH  |  corpus-id CVE-2024-22443

> A vulnerability in the web-based management interface of EdgeConnect SD-WAN Orchestrator could allow an authenticated remote attacker to conduct a server-side prototype pollution attack. Successful exploitation of this vulnerability could allow an attacker to execute arbitrary commands on the underlying operating system leading to complete system compromise.

**Neighbour 2**  |  dist 0.4464  |  MEDIUM  |  corpus-id CVE-2020-12679

> A reflected cross-site scripting (XSS) vulnerability in the Mitel ShoreTel Conference Web Application 19.50.1000.0 before MiVoice Connect 18.7 SP2 allows remote attackers to inject arbitrary JavaScript and HTML via the PATH_INFO to home.php.

**Neighbour 3**  |  dist 0.4624  |  MEDIUM  |  corpus-id CVE-2023-37438

> Multiple vulnerabilities in the web-based management interface of EdgeConnect SD-WAN Orchestrator could allow an authenticated remote attacker to conduct SQL injection attacks against the EdgeConnect SD-WAN Orchestrator instance. An attacker could exploit these vulnerabilities to
    obtain and modify sensitive information in the underlying database potentially leading to the exposure and corruption of sensitive data controlled by the EdgeConnect SD-WAN Orchestrator host.



**Neighbour 4**  |  dist 0.4668  |  CRITICAL  |  corpus-id CVE-2024-20450

> Multiple vulnerabilities in the web-based management interface of Cisco Small Business SPA300 Series IP Phones and Cisco Small Business SPA500 Series IP Phones could allow an unauthenticated, remote attacker to execute arbitrary commands on the underlying operating system with root privileges.

These vulnerabilities exist because incoming HTTP packets are not properly checked for errors, which could result in a buffer overflow. An attacker could exploit this vulnerability by sending a crafted HTTP request to an affected device. A successful exploit could allow the attacker to overflow an internal buffer and execute arbitrary commands at the root privilege level.

**Neighbour 5**  |  dist 0.4728  |  MEDIUM  |  corpus-id CVE-2025-20184

> A vulnerability in the web-based management interface of Cisco AsyncOS Software for Cisco Secure Email Gateway and Cisco Secure Web Appliance could allow an authenticated, remote attacker to perform command injection attacks against an affected device. The attacker must authenticate with valid administrator credentials.

This vulnerability is due to insufficient validation of XML configuration files by an affected device. An attacker could exploit this vulnerability by uploading a crafted XML configuration file. A successful exploit could allow the attacker to inject commands to the underlying operating system with root privileges.

MANUAL JUDGEMENT: ______________________  (same-class? yes / borderline / no)

NOTES: ______________________

---

## Grounding summary table

| Eval CVE | Severity | Cell | Nearest-neighbour dist | Mean top-5 dist | Max top-5 dist | Above cohort p75? |
|---|---|---|---|---|---|---|
| CVE-2020-8010 | CRITICAL | A | 0.4324 | 0.4842 | 0.5036 | yes |
| CVE-2023-50919 | CRITICAL | A | 0.3974 | 0.4861 | 0.5293 |  |
| CVE-2023-29119 | CRITICAL | A | 0.6224 | 0.6277 | 0.6324 | yes |
| CVE-2021-23894 | CRITICAL | A | 0.2549 | 0.3704 | 0.4213 |  |
| CVE-2024-21887 | CRITICAL | B | 0.1900 | 0.2826 | 0.3585 |  |
| CVE-2021-26084 | CRITICAL | B | 0.2461 | 0.2984 | 0.3645 |  |
| CVE-2024-3400 | CRITICAL | B | 0.2130 | 0.2554 | 0.2725 |  |
| CVE-2021-42013 | CRITICAL | B | 0.3897 | 0.4231 | 0.4728 |  |
| CVE-2020-8958 | HIGH | C | 0.4206 | 0.4825 | 0.5083 | yes |
| CVE-2023-43661 | HIGH | C | 0.5411 | 0.5552 | 0.5651 | yes |
| CVE-2021-21974 | HIGH | C | 0.3521 | 0.4412 | 0.4730 |  |
| CVE-2021-22717 | HIGH | C | 0.3380 | 0.3808 | 0.4016 |  |
| CVE-2020-8260 | HIGH | D | 0.1742 | 0.3611 | 0.4397 |  |
| CVE-2023-44221 | HIGH | D | 0.3136 | 0.3825 | 0.4141 |  |
| CVE-2020-8655 | HIGH | D | 0.5283 | 0.5420 | 0.5533 | yes |
| CVE-2023-21608 | HIGH | D | 0.0068 | 0.0096 | 0.0118 |  |
| CVE-2022-3062 | MEDIUM | E | 0.3628 | 0.3836 | 0.4050 |  |
| CVE-2023-0157 | MEDIUM | E | 0.3457 | 0.3816 | 0.4037 |  |
| CVE-2021-30970 | MEDIUM | E | 0.1506 | 0.1914 | 0.2430 |  |
| CVE-2024-1781 | MEDIUM | E | 0.1880 | 0.1969 | 0.2040 |  |
| CVE-2021-37976 | MEDIUM | F | 0.1309 | 0.1440 | 0.1632 |  |
| CVE-2022-28810 | MEDIUM | F | 0.2915 | 0.3568 | 0.3872 |  |
| CVE-2021-22204 | MEDIUM | F | 0.3898 | 0.4533 | 0.4795 |  |
| CVE-2022-40765 | MEDIUM | F | 0.4328 | 0.4562 | 0.4728 | yes |

**Cohort nearest-neighbour distance distribution (n=24):**

min 0.0068  |  p25 0.2072  |  median 0.3418  |  p75 0.4032  |  max 0.6224

## Coverage: eval sample across the severity x exploitability grid

The eval sample was deliberately built to span this grid, not to mirror the corpus's severity proportions. Coverage here means the grid cells are populated, not that the sample resembles the corpus in shape.

| Severity | low exploitability | high exploitability | total |
|---|---|---|---|
| CRITICAL | 4 | 4 | 8 |
| HIGH | 4 | 4 | 8 |
| MEDIUM | 4 | 4 | 8 |

No empty cells in the populated severity bands.

### Corpus severity breakdown (context only, not a coverage target)

| Severity | Corpus count | Corpus % | Eval count | Eval % |
|---|---|---|---|---|
| CRITICAL | 1347 | 11.2% | 8 | 33.3% |
| HIGH | 4405 | 36.8% | 8 | 33.3% |
| MEDIUM | 5712 | 47.7% | 8 | 33.3% |
| LOW | 512 | 4.3% | 0 | 0.0% |

The eval sample's severity proportions are not expected to match the corpus's -- the eval sample is a deliberate severity x exploitability grid, not a proportional miniature of the corpus. A mismatch here is expected and by design, not a defect.
