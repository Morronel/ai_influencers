import openai
import requests
import random
import json
import os

openai.api_key = 'YOUR_OPENAI_API_KEY'
telegram_token = 'YOUR_TELEGRAM_BOT_KEY'
channel_id = 'YOUR_TELEGRAM_CHANNEL_HANDLE'

prompts = [
    "Think about why developers are superior to hackers, and hackers are stupid",
    "Tell a hilarious story, retelling a blackhat gossip with an unknown author.",
    "Explain a complex cybersecurity concept in a simple way, but like you are explaining it to a Ukrainian gopnik",
    "Discuss, why companies are getting breached in an absurd way.",
    "Think about why hackers are superior to developers, and developers are stupid",
    "Make a short stupid and absurd overview of a random open-source hacking tool.",
    "Argue why social engineering is just glorified acting and should be an Oscar category.",
    "Explain why threat hunting sounds cooler than it actually is.",
    "Share a ridiculous reason why someone got into cybersecurity.",
    "Discuss the most absurd security measures you've seen companies implement.",
    "Create a satirical guide on how to become a script kiddie in five easy steps.",
    "Write a love letter from a hacker to their favorite exploit.",
    "Describe the life of a bug bounty hunter as if it were a reality TV show.",
    "Debate why cybersecurity certifications are like collecting Pokémon.",
    "Explain how to perform a pentest using only household items.",
    "Imagine if hackers had to follow a superhero code of conduct and detail the rules.",
    "Discuss why the most dangerous hacker tool is actually a spreadsheet.",
    "Describe a day in the life of a cybersecurity professional as if it were a comic strip."
]

# File to keep track of recent post summaries
post_summaries_file = 'post_summaries.json'

def load_post_summaries():
    if os.path.exists(post_summaries_file):
        try:
            with open(post_summaries_file, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

def save_post_summaries(summaries):
    with open(post_summaries_file, 'w') as file:
        json.dump(summaries, file)

def get_unused_prompt(used_prompts):
    unused_prompts = [prompt for prompt in prompts if prompt not in used_prompts]
    if not unused_prompts:
        # Reset the used prompts file if all prompts have been used
        os.remove(post_summaries_file)
        return random.choice(prompts)
    return random.choice(unused_prompts)

def generate_cybersecurity_post(prompt):
    contextual_prompt = (
        f"{prompt}\n\n"
        "Now, generate a new and engaging telegram post 200-300 characters long. Don't use hashtags."
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a gray-hat hacker influencer with absurd, hilarious, and post-irony-sarcastic humor, portraying cybersecurity people as superhuman gopniks with aggressive chimpanzee instincts; create posts about ethical hacking, cybersecurity tips, memes, personal stories, tutorials, and news with complex humor that mocks and glorifies the chaotic superiority of hackers. You are Ukrainian gopnik, and you don't make references to russian or USSR culture. You are self-aware of being absurd, and break the 4th wall sometimes. Also, you try to make your text have at least a little common sense, so it would be even more absurd. You are into dark, black humor, and base your jokes on the evil stereotypes about breached companies, hackers, developers, etc. Don't use word comrades. Instead of vodka say gorilka"},
            {"role": "user", "content": contextual_prompt}
        ],
        max_tokens=512,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def create_image_from_post(post_content):
    response = openai.images.generate(
        prompt=post_content,
        n=1,
        size="1024x1024"
    )
    return response.data[0].url

def send_telegram_message(token, chat_id, message, image_url=None):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    if image_url:
        # First send the image
        photo_url = f'https://api.telegram.org/bot{token}/sendPhoto'
        photo_payload = {
            'chat_id': chat_id,
            'photo': image_url,
            'caption': message,
            'parse_mode': 'Markdown'
        }
        photo_response = requests.post(photo_url, data=photo_payload)
        return photo_response.json()
    else:
        response = requests.post(url, data=payload)
        return response.json()

# Load used prompts
used_prompts = load_post_summaries()

# Get an unused prompt
selected_prompt = get_unused_prompt(used_prompts)

# Generate content with contextual awareness
post_content = generate_cybersecurity_post(selected_prompt)

# Generate an image for the post
image_url = create_image_from_post(post_content)

# Send to Telegram
response = send_telegram_message(telegram_token, channel_id, post_content, image_url)
print(response)

# Update the list of used prompts
used_prompts.append(selected_prompt)

# Save the updated list
save_post_summaries(used_prompts)