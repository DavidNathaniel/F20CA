# To my team members:

##### step1:

Before using, run the following command:

```python
$ python setup.py install
```

##### step2:

Microsoft Visual C++ 14.0 or greater is required.

Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

##### step3:

At the same time, you need to have the following libraries:

```
prophet
Retico
retico-core
pyaudio
flexx
google-cloud-speech~=2.15
rasa-nlu
torch==1.13.1
transformers
webrtcvad
speechbrain
pydantic
httpx
distro
```

##### Step 4:
API keys (ASR, GPT etc.) are held within a ReticoGPT folder inside k.env file. This can be provided upon request, however most of the information is availble on our Teams page.

##### Info: GIT Branch commands to fetch and switch:
`git fetch <remote_name> <branch_name>`
`git branch <branch_name> FETCH_HEAD`
`git checkout <branch_name>`

# Start

run app.py

