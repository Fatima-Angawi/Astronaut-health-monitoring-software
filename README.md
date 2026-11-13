# Astronaut-health-monitoring-software

As stated in the Evidence Report:

Risk of Inadequate Human-System Integration Architecture:
"We must understand the types of tasks that astronauts will likely perform autonomously, and
develop human-system integration standards and guidelines for the needed tools and mitigation
strategies that ensure success in performing those tasks on an autonomous mission."
We develop this software to integrate these standards and guidelines to deliver an app that can simplify
the process of monitoring, warning and protecting astronaunt health during their space missions  

## Data availability
We ran 33 systematic queries on NASA OSDR (355 unique studies). 
No open dataset contained human sleep, PVT, mood, heart rate, blood pressure, or SpO₂.
The only human spaceflight data (Inspiration4) is molecular and clinical blood data. https://osdr.nasa.gov/bio/repo/data/studies/OSD-569
Therefore crew indicators are simulated from HRP Evidence Report values; environment data (radiation, CO₂, SPE) is real NASA data.

---
## # Task: SEP Data preparation and pipeline
description: SEP is one of the inputs that needs to be watched for radiation risk warning
DONKI.py represents the ground-based space weather alert; in a real mission, this would come from mission control.


assigned to: Fatima Angawi


## # Task: Behavioral / Cognitive Changes Id: R02e and R02e in sheet
description:
solid understanding and data input

assigned to: Layan 


## # Task: R18 bone fracture check indicator column for guidance 
description:
solid understanding and data input

Average density loss	1–1.5% per month

Projected bone loss = months in flight × loss rate, using the with-ARED rate if exercise is logged and the pre-ARED rate if not (Table 4, p22). That shows the astronaut, with evidence, what missed exercise costs.

later:
(for context) Mission phase: microgravity / Moon / Mars / return
in-app feature: Vitamin D supplement (taken / not taken)

assigned to: LAYAN 


## # Task: R10b	Cardiovascular Adaptations
description:


assigned to: Fatima Angawi


## # Task: hustle closed environment
description:
look for data

assigned to: 


## # Task: sleep loss indicators 
description:
look for data

assigned to: Afnan Alsharif




## # Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)

---

## # About the Project (Heading 2)

Provide a brief introduction to the project. Explain the motivation behind building it, the technologies used, and what makes it unique.

### # Built With (Heading 3)



---

## # Features (Heading 2)

Highlight the core functionalities and capabilities of your application or model.


---

## # Getting Started (Heading 2)


### # Prerequisites (Heading 3)

List any software, libraries, or API keys needed before installation.


### # Installation (Heading 3)

Step-by-step instructions on how to install and set up the project:

1. Clone the repository:
   ```bash
  
