#import xml.etree.ElementTree as ET
import openai
import json
from flask import Flask, request, render_template
import re
import requests
from urllib.parse import quote
import time
from colorama import Fore


example_text = """
I'd be glad to help you with that! Here are some paper references related to lifelong learning in reinforcement learning (RL):

Parisotto, E., & Rusu, A. A. (2017). Neural Map: Structured Memory for Deep Reinforcement Learning. arXiv preprint arXiv:1702.08360. Link
Wang, J. X., Kurth-Nelson, Z., Kumaran, D., Tirumala, D., Soyer, H., Leibo, J. Z., ... & Botvinick, M. (2016). Learning to reinforcement learn. arXiv preprint arXiv:1611.05763. Link
Wang, T., Cao, Y., Xu, Z., Chen, J., & Xu, H. (2020). Learning to Remember: A Lifelong Learning Reinforcement Learning Approach. In Proceedings of the 37th International Conference on Machine Learning (ICML). Link
Ritter, S., Foerster, J., Mottaghi, R., Hausman, K., Tamar, A., Bergstra, J., ... & Abbeel, P. (2018). Been there, done that: Meta-learning with episodic recall. arXiv preprint arXiv:1805.09692. Link
Rusu, A. A., Rabinowitz, N. C., Desjardins, G., Soyer, H., Kirkpatrick, J., Kavukcuoglu, K., ... & Hadsell, R. (2016). Progressive neural networks. arXiv preprint arXiv:1606.04671. Link
Mankowitz, D. J., Li, Y., Tamar, A., Yang, A., Guez, A., McClelland, J. L., & Mannor, S. (2018). Learning latent dynamics for planning from pixels. arXiv preprint arXiv:1811.04551. Link
Parisotto, E., Ba, J. L., & Rusu, A. A. (2018). Stable value estimation with state-regularized recurrent nets. arXiv preprint arXiv:1810.01491. Link
Castro, P. S., & Aggarwal, K. (2018). The option-critic architecture. In Proceedings of the 35th International Conference on Machine Learning (ICML). Link
Riemer, M., Cases, I., Viola, F., & Prendinger, H. (2021). Lifelong Reinforcement Learning: A Review. IEEE Transactions on Cognitive and Developmental Systems. Link
Please note that availability and access to these papers may vary. Some of them may also have newer versions or related papers, so it's a good idea to explore the authors' profiles or related research for the most up-to-date information in the field of lifelong learning in reinforcement learning.
"""


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        text = request.form['text']
        result = compare_text(text)

    return render_template('index.html', result=result)

openai.api_key = '' # Your api key here

def prompt_openai(prompt):
    #prompt = f"Given the following input:\n{input_text}\n\nPlease provide relevant papers related to lifelong learning in reinforcement learning."
    response = openai.Completion.create(
        engine="text-davinci-003",  # You can use the GPT-3 engine of your choice
        prompt=prompt,
        max_tokens=1000  # Adjust this based on your needs
    )
    output_text = response.choices[0].text
    print(output_text)
    output_text = compare_text(output_text)
    return output_text

def compare_text(text):
    results = ''

    # Uncomment for direct querying of OpenAI API
    #text = prompt_openai(text)

    lines = text.split('\n')
    #pattern = r"([A-Za-z\s.,&]+)\s\((\d{4})\)\.\s(.*?)(?=\.\s|\.\sLink|$)"
    pattern = r"([A-Za-z\s.,&\-]+)\s\((\d{4})\)\.\s(.*?)(?=\.\s|\.\sLink|$)"

    for line in lines:
        matches = re.findall(pattern, line)
        for match in matches:
            au, yr, ti = match
            
            # Use the DataCite API to fetch metadata
            url = f'https://api.datacite.org/dois?query=titles.title:(%22{quote(ti.lower())}%22)'
            response = requests.get(url)
            data = response.json()

            # Check if any valid entries are found in the DataCite response
            if 'data' not in data or len(data['data']) == 0:
                results += (f'<span style="color: red;">Possibly generated</span>\n')
                results += (f'<span style="color: red;">Generated paper title: {ti}</span>\n')
                results += (f'<span style="color: red;">Generated paper author(s): {au}</span>\n')
                results += (f'<span style="color: red;">Generated paper submission year: {yr}</span>\n')
                results += ('-----------------\n\n')
                continue

            all_results = data['data']

            for result in all_results:
                # Extract relevant information from the DataCite response
                entry = result#data['data'][0]
                title = entry['attributes']['titles'][0]['title']
                authors = [contributor['name'] for contributor in entry['attributes']['creators']]
                doi = entry['attributes']['doi']
                
                # Extract last names from authors
                input_last_names = re.sub(r'\w\.\s*', '', au.replace(' ...', '').replace(' &', '')).replace(' , ', '').replace(', ', '').split(',')
                api_last_names = [name.split(', ')[0] for name in authors]

                if title.strip().lower() != ti.strip().lower():
                    continue  # Skip this iteration if the titles don't match
                
                # Check if the fetched last names match the input last names
                results += (f'Title (Text): {ti}\n')
                results += (f'Title (DataCite):  {title}\n')
                #if title.strip().lower() == ti.strip().lower():
                #    print(Fore.GREEN + "(matches to input)" + Fore.WHITE)
                #else:
                #    print(Fore.RED + "(does not match)" + Fore.WHITE)
                    
                results += (f"Author(s): {', '.join(authors)}\n")
                
                all_names_match = True
                mismatched_input_last_names_formatted = []
                mismatched_api_last_names_formatted = []
                for input_name in input_last_names:
                    if input_name.lower() not in [api_name.lower() for api_name in api_last_names]:
                        mismatched_input_last_names_formatted.append(f'<span style="color: red;">{input_name}</span>')
                    else:
                        mismatched_input_last_names_formatted.append(f'<span style="color: green;">{input_name}</span>')
                
                for api_name in api_last_names:
                    if api_name.lower() not in [input_name.lower() for input_name in input_last_names]:
                        mismatched_api_last_names_formatted.append(f'<span style="color: red;">{api_name}</span>')
                    else:
                        mismatched_api_last_names_formatted.append(f'<span style="color: green;">{api_name}</span>')

                
                #if not all_names_match:
                results += (f"Last names from input: {' | '.join(mismatched_input_last_names_formatted)}\n")
                results += (f"Last names from DataCite: {' | '.join(mismatched_api_last_names_formatted)}\n")
                    
                results += (f"Submission year (Text): {yr}\n")
                results += (f"DOI (DataCite): {doi}\n")
                results += ('-----------------\n\n')
                #time.sleep(4)
    return results

if __name__ == '__main__':
    app.run(debug=True)
