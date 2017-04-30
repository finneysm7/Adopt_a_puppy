from flask import Flask, request, session
from twilio import twiml
import os
import petfinder

# The session object makes use of a secret key.
SECRET_KEY = 'a_secret_key'

app = Flask(__name__)
app.config.from_object(__name__)



api = petfinder.PetFinderClient(api_key=os.environ['api_key'],
                               api_secret=os.environ['api_secret']
                               )


@app.route("/", methods=['GET','POST'])
def shelter_or_pet():
    if request.values.get('Body', None):
        text = request.values.get('Body', None).encode('utf-8')
    else:
        text = 'default'
    if text is not None and session.get('shelterId'):
        if 'I want to adopt' in text:
            return send_shelter()
        elif 'next' in text or 'more' in text or 'pass' in text:
            return send_pet()
        else:
            resp = twiml.Response()
            resp.message("Please type next, more or pass to see more pets")
            return str(resp)
    else:
        return send_pet()

def send_pet():
    """Get a info about a pet and send it via a message"""
    pet = api.pet_getrandom(output='basic')
    shelter_id = pet['shelterId']
    pet = clean_pet(pet)
    session['shelterId'] = shelter_id
    resp = twiml.Response()
    with resp.message("Adopt this pet?\nname: %s\n" % pet['name']
                      + "breed: %s\n" % pet['breeds']
                      + "location: %s\n" % get_location(shelter_id)
                      + "description: %s" % pet['description']
                      ) as m:
        m.media(pet['photo'])
    return str(resp)

def send_shelter():
    #Send shelter info for a pet via session info
    resp = twiml.Response()
    shelter = api.shelter_get(id=session['shelterId'])
    shelter = clean_shelter(shelter)
    if shelter:
        resp.message("Shelter Info:\n"
                     + "phone number: %s\n" % shelter['phone']
                     + "email: %s\n" %shelter['email']
                     )
    else:
        resp.message('The shelter for that pet was not found.')
    return str(resp)

def get_location(shelter):
    #get location based on pet
    shelt = api.shelter_get(id=shelter)
    shelt = clean_shelter(shelt)
    if shelt:
        location = shelt['name'] + ' ' + shelt['city'] + ' ' + shelt['zip']
    else:
        location = "Shelter not found"
    return location

def clean_pet(pet):
    result = {}
    if pet.get('name'):
        result['name'] = pet.get('name').encode('utf-8')
    else:
        result['name'] = ''
    if pet.get('breeds'):
        result['breeds'] = " ".join(pet['breeds']).encode('utf-8')
    else:
        result['breeds'] = ''
    if pet.get('description'):
        result['description'] = pet['description'].encode('utf-8')
    else:
        result['description'] = ''
    if len(pet.get('photos')) >= 4:
        result['photo'] = pet.get('photos')[3]['url']
    elif pet.get('photos'):
        result['photo'] = pet.get('photos')[0]['url']
    else:
        result['photo'] = 'http://www.petfinder.com/banner-images/widgets/40.jpg'
    return result

def clean_shelter(shelter):
    result = {}
    if shelter.get('name'):
        result['name'] = shelter.get('name').encode('utf-8')
    else:
        result['name'] = ''
    if shelter.get('city'):
        result['city'] = shelter.get('city').encode('utf-8')
    else:
        result['city'] = ''
    if shelter.get('zip'):
        result['zip'] = shelter.get('zip').encode('utf-8')
    else:
        result['zip'] = ''
    if shelter.get('phone'):
        result['phone'] = shelter.get('phone').encode('utf-8')
    else:
        result['phone'] = ''
    if shelter.get('email'):
        result['email'] = shelter.get('email').encode('utf-8')
    else:
        result['email'] = ''
    return result


if __name__ == "__main__":
    app.run(debug=True)
