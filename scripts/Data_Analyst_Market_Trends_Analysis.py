#!/usr/bin/env python
# coding: utf-8

# In[5]:


import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc
from datetime import datetime, timedelta
from collections import Counter


# In[1]:


# WEB SCRAPING NAUKRI.COM

def parse_date(text):  # Method for retrieving Date Posted Category values 

    today = datetime.today()
    text = text.lower().strip()

    category = 'Unknown' # Default Value
    parsed_date = None # Default Value

    if 'Just now' in text or 'hour' in text:
        parsed_date = today.date()
        category = 'Today'

    elif 'day' in text:
        try:
            num_days = int(text.split()[0])
            parsed_date = (today - timedelta(days=num_days)).date() # Retrieves the correct date based on the calculation (today_date - retrieved_date)
            category = 'Last 7 days' if num_days<=7 else 'Older'
        except:
            pass

    elif 'week' in text:
        try:
            str_weeks = text.split()[0].replace('+', '')
            num_weeks = int(str_weeks)
            parsed_date = (today - timedelta(weeks=num_weeks + (1 if '+' in text else 0))).date() # Retrieves the correct date based on the calculation (today_date - retrieved_date)
            category = '2-4 weeks' if num_weeks<=4 else 'Older'
        except:
            pass

    else:
        category = 'Unknown'

    return parsed_date, category


options_n = uc.ChromeOptions()
#options.headless = True ** Disabled headless option to avoid IP blocking **
options_n.add_argument("--no-sandbox")
options_n.add_argument("--disable-dev-shm-usage")

driver_n = uc.Chrome(options_n=options_n)

base_url = 'https://www.naukri.com/data-analyst-jobs-in-hyderabad-secunderabad' # Naukri.com URL for retrieving Data Analyst Job postings 

job_list_n = []

for page in range(1, 6):
    print(f'Scraping page {page}')
    if page == 1:
        url_n = base_url
    else:
        url_n = f"{base_url}-{page}"

    driver_n.get(url_n)

    # Try-Except block for avoiding and handling exceptions like server overuse/overload and avoid IP blocking
    try:
        WebDriverWait(driver_n, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper")))
        print("Job cards loaded.")
        time.sleep(2)
    except:
        print(f"No Job cards found on page {page}.")
        continue

    jobs_n = driver_n.find_elements(By.CLASS_NAME, 'srp-jobtuple-wrapper') # Find all the elements by class name
    print(f"Found {len(jobs_n)} job cards on page {page}")

    # Retrieving value of the specific element by either class name or CSS tag
    for job in jobs_n:
        try:
            title = job.find_element(By.CSS_SELECTOR, 'h2 a[title]').get_attribute("title")
        except:
            title = 'N/A'

        try:
            company = job.find_element(By.CSS_SELECTOR, 'a[class*="comp-name"]').text
        except:
            company = 'N/A'

        try:
            experience = job.find_element(By.CLASS_NAME, 'expwdth').text
        except:
            experience = 'N/A'

        try:
            location = job.find_element(By.CLASS_NAME, 'locWdth').text
        except:
            location = 'N/A'

        try:
            skills_ul = job.find_element(By.CLASS_NAME, 'tags-gt')
            skill = skills_ul.find_elements(By.TAG_NAME, 'li' )
            skills = ','.join([s.text.strip() for s in skill if s.text.strip() != ''])
        except:
            skills = 'N/A'

        try:
            date_posted_element = job.find_element(By.CLASS_NAME, 'job-post-day').text.strip()
            date_posted, date_posted_category = parse_date(date_posted_element)
        except:
            date_posted, date_posted_category = None, 'Unknown'

        # Appending the retrieved elements to the jobs list
        job_list_n.append({
            'Title': title,
            'Company': company,
            'Location': location,
            'Experience Required': experience,
            'Skills Required': skills,
            'Date Posted': date_posted,
            'Date Posted Category': date_posted_category
        })

        time.sleep(3)

driver_n.quit()

df_n = pd.DataFrame(job_list_n) # Creating DataFrame using the jobs list
print(f'Scraping Complete!\nTotal Jobs collected: {len(df_n)}')


# In[79]:


df_n


# In[100]:


# Creating Job Type column for categorizing the retrieved jobs based on the job type (On-Site/Remote/Hybrid) using the values of Location column   
def job_type(location):
    location = location.lower()
    if 'remote' in location:
        return 'Remote'
    elif 'hybrid' in location:
        return 'Hybrid'
    else:
        return 'On-Site'

df_n['Job Type'] = df_n['Location'].apply(job_type)


# In[101]:


df_n['Job Type'].value_counts()


# In[102]:


df_n[(df_n['Job Type'] == 'Hybrid')]


# In[103]:


# Creating Experience column for categorizing the retrieved jobs based on the experience required (Entry-Level/Mid-Level/Senior-Level/Executive) using the values of Experience Required column
def exp_req(experience):
    experience = experience.split()[0].replace('-', ' ')
    exp = int(experience.split()[0])

    if exp<=1:
        return 'Entry-Level'
    elif exp>=2 and exp<=5:
        return 'Mid-Level'
    elif exp>=5 and exp<=10:
        return 'Senior-Level'
    else:
        return 'Executive'

df_n['Experience Categeory'] = df_n['Experience Required'].apply(exp_req)


# In[106]:


df_n['Experience Categeory'].value_counts()


# In[104]:


df_n[(df_n['Experience Categeory'] == 'Executive')]


# In[107]:


# Creating a DataFrame for showing the most in-demand skills based on the values retrieved from the Skills Required column of the original DataFrame 
skill_series = df_n['Skills Required']
skills_list = []
for skills in skill_series:
    skills_split = [skill.strip().title() for skill in skills.split(',') if skill.strip()]
    skills_list.extend(skills_split)

skill_count = Counter(skills_list)

skill_df = pd.DataFrame(skill_count.items(), columns=['Skill','Count']).sort_values(by='Count', ascending=False)


# In[108]:


skill_df.head(10)


# In[70]:


df_n.columns 


# In[109]:


# Rearranging columns of the original DataFrame
ordered_rows = ['Title', 'Company', 'Location', 'Job Type', 'Date Posted Category', 'Date Posted',
                'Skills Required', 'Experience Required', 'Experience Categeory']
df_n = df_n[ordered_rows]


# In[110]:


df_n


# In[112]:


df_n.to_csv('Naukri.com_DA_HYD.csv', index=False) # Exporting the original DataFrame to a .csv file


# In[116]:


skill_df.to_csv('Naukri.com_DA_HYD_Skills.csv', index=False) # Exporting the skills DataFrame to a .csv file

