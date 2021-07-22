import facebook,json
token= {"EAAgEjhopC7UBAM7B6oBq5T0SeQwLZBSm9p6XAtu3dbIiNYImcj3OivVZBkOulDLEptVAhiYgsaq2LSktCM54JKcqF0QJmY1Cp6sEwugQz5wWZCZBSP2p4jw9qU5wZCaK2ZCUHZCK5Nz18TCM1R7XpOI8W6z07MrHZBZA8YoqpcAIhezuBpNWI5ZCjmocfrcFDvOJUZD"}
graph = facebook.GraphAPI(token)
fields = ['email','name','picture']
profile = graph.get_object('me',fields=fields)

print(json.dumps(profile,indent=4))