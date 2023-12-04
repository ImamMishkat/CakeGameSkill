# -*- coding: utf-8 -*-

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

import json
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective)

import os
import boto3
import json

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor


# are you tracking past celebrities between sessions
CELEB_TRACKING = True


from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.services import ServiceException


from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        """
        device_id = handler_input.request_envelope.context.system.device.device_id
        
        #gets device id
        sys_object = handler_input.request_envelope.context.system
        device_id = sys_object.device.device_id
        
        #gets Alexa settings API info 
        api_endpoint = sys_object.api_endpoint
        api_access_token = sys_object.api_access_token
        
        # construct systems api timezone url
        url = '{api_endpoint}/v2/devices/{device_id}/settings/System.timeZone'.format(api_endpoint=api_endpoint, device_id=device_id)
        headers = {'Authorization': 'Bearer ' + api_access_token}

        user_time_zone = ""
        try:
            r = requests.get(url, headers=headers)
            res = r.json()
            logger.info("Device API result: {}".format(str(res)))
            user_time_zone = res
        except Exception:
            handler_input.response_builder.speak("There was a problem connecting to the service")
            return handler_input.response_builder.response
         """   
        greeting = ""
        user_time_zone = ""
        
        
        """
        try:
            user_preferences_client = handler_input.service_client_factory.get_ups_service()
            user_time_zone = user_preferences_client.get_system_time_zone(device_id)
        except Exception as e:
            user_time_zone = 'error.'
            logger.error(e)
        """   
        
        if user_time_zone == 'error':
            greeting = 'Hello.'
        else:
            from celebrityFunctions import get_hour
            hour = get_hour()
            #hour = get_hour(user_time_zone) 
            if 0 <= hour and hour <= 4:
                greeting = "Hi night-owl!"
            elif 5 <= hour and hour <= 11:
                greeting = "Good morning!"
            elif 12 <= hour and hour <= 17:
                greeting = "Good afternoon!"
            elif 17 <= hour and hour <= 23:
                greeting = "Good evening!"
            else:
                greeting = "Howdy partner!" 
        
        speak_output = ''
        session_attributes = handler_input.attributes_manager.session_attributes

        if session_attributes["visits"] == 0:
            speak_output = f"{greeting} Welcome to Cake Game. " \
                f"I'll tell you a celebrity name and you try " \
                f"to guess the month and year they were born. " \
                f"See how many you can get! " \
                f"Would you like to play?"
        else:
            speak_output = f"{greeting} Welcome back to Cake Game! " \
                f"Ready to guess some more celebrity birthdays?"

        # increment the number of visits and save the session attributes so the
        # ResponseInterceptor will save it persistently.
        session_attributes["visits"] = session_attributes["visits"] + 1


        #====================================================================
        # Add a visual with Alexa Layouts
        #====================================================================

        # Import an Alexa Presentation Language (APL) template
        with open("./documents/APL_simple.json") as apl_doc:
            apl_simple = json.load(apl_doc)

            if ask_utils.get_supported_interfaces(
                    handler_input).alexa_presentation_apl is not None:
                handler_input.response_builder.add_directive(
                    RenderDocumentDirective(
                        document=apl_simple,
                        datasources={
                            "myData": {
                                #====================================================================
                                # Set a headline and subhead to display on the screen if there is one
                                #====================================================================
                                "Title": 'Say "yes."',
                                "Subtitle": 'Play some Cake Game.',
                            }
                        }
                    )
                )

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class PlayGameHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
                and ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # get the current session attributes, creating an object you can read/update
        session_attributes = handler_input.attributes_manager.session_attributes

        speak_output = ''

        # check if there's a current celebrity. If so, repeat the question and exit.
        if session_attributes["current_celeb"] != None:

            speak_output = f'In what month and year was {session_attributes["current_celeb"]["name"]} born?'
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )

        # Import the celebrity functions and get a random celebrity.
        from celebrityFunctions import get_random_celeb
        celeb = get_random_celeb(session_attributes["past_celebs"])
        title = celeb["name"]
        subtitle = 'What month and year were they born?'

        # Check to see if there are any celebrities left.
        if celeb["id"] == 0:
            speak_output = 'You have run out of celebrities. Thanks for playing!'
            title = 'Game Over'
            subtitle = ''
        else:
            # set the "current_celeb" attribute
            session_attributes["current_celeb"] = celeb

            # save the session attributes
            handler_input.attributes_manager.session_attributes = session_attributes

            # Ask the question
            speak_output = f'In what month and year was {celeb["name"]} born?'

        #====================================================================
        # Add a visual with Alexa Layouts
        #====================================================================

        # Import an Alexa Presentation Language (APL) template
        with open("./documents/APL_simple.json") as apl_doc:
            apl_simple = json.load(apl_doc)

            if ask_utils.get_supported_interfaces(
                    handler_input).alexa_presentation_apl is not None:
                handler_input.response_builder.add_directive(
                    RenderDocumentDirective(
                        document=apl_simple,
                        datasources={
                            "myData": {
                                #====================================================================
                                # Set a headline and subhead to display on the screen if there is one
                                #====================================================================
                                "Title": title,
                                "Subtitle": subtitle,
                            }
                        }
                    )
                )

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class GetBirthdayIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
                and ask_utils.is_intent_name("GetBirthdayIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = ''

        # get the current session attributes, creating an object you can read/update
        session_attributes = handler_input.attributes_manager.session_attributes

        # if there's a current_celeb attribute but it's None, or there isn't one
        # error, cue them to say "yes" and end

        if session_attributes["current_celeb"] == None:

            speak_output = "I'm sorry, there's no active question right now. Would you like a question?"

            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )

        # Get the slot values
        year = ask_utils.request_util.get_slot(handler_input, "year").value
        month = ask_utils.request_util.get_slot(handler_input, "month").value

        # Okay, check the answer
        from celebrityFunctions import check_answer
        winner = check_answer(
            session_attributes["current_celeb"],
            month,
            year
        )

        # Add the celebrity to the list of past celebs.
        # Store the value for the rest of the function,
        # and set the current celebrity to None
        session_attributes["past_celebs"].append(session_attributes["current_celeb"])
        cname = session_attributes["current_celeb"]["name"]
        session_attributes["current_celeb"] = None

        # We'll need variables for our visual. Let's initialize them.
        title = ''
        subtitle = ''

        # Did they get it?
        if winner:
            session_attributes["score"] = session_attributes["score"] + 1
            title = 'Congratulations!'
            subtitle = 'Wanna go again?'
            speak_output = f"Yay! You got {cname}'s birthday right! Your score is now " \
                f"{session_attributes['score']}. Want to try another?"
        else:
            title = 'Awww shucks'
            subtitle = 'Another?'
            speak_output = f"Sorry. You didn't get the right month and year for " \
                f"{cname}. Maybe you'll get the next one. Want to try another?"

        # store all the updated session data
        handler_input.attributes_manager.session_attributes = session_attributes

        #====================================================================
        # Add a visual with Alexa Layouts
        #====================================================================

        # Import an Alexa Presentation Language (APL) template
        with open("./documents/APL_simple.json") as apl_doc:
            apl_simple = json.load(apl_doc)

            if ask_utils.get_supported_interfaces(
                    handler_input).alexa_presentation_apl is not None:
                handler_input.response_builder.add_directive(
                    RenderDocumentDirective(
                        document=apl_simple,
                        datasources={
                            "myData": {
                                #====================================================================
                                # Set a headline and subhead to display on the screen if there is one
                                #====================================================================
                                "Title": title,
                                "Subtitle": subtitle,
                            }
                        }
                    )
                )

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class LoadDataInterceptor(AbstractRequestInterceptor):
    """Check if user is invoking skill for first time and initialize preset."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes

        # ensure important variables are initialized so they're used more easily in handlers.
        # This makes sure they're ready to go and makes the handler code a little more readable
        if 'current_celeb' not in session_attributes:
            session_attributes["current_celeb"] = None

        if 'score' not in session_attributes:
            session_attributes["score"] = 0

        if 'past_celebs' not in persistent_attributes:
            persistent_attributes["past_celebs"] = []

        if 'past_celebs' not in session_attributes:
            session_attributes["past_celebs"] = []

        # if you're tracking past_celebs between sessions, use the persistent value
        # set the visits value (either 0 for new, or the persistent value)
        session_attributes["past_celebs"] = persistent_attributes["past_celebs"] if CELEB_TRACKING else session_attributes["past_celebs"]
        session_attributes["visits"] = persistent_attributes["visits"] if 'visits' in persistent_attributes else 0

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug('----- REQUEST -----')
        logger.debug("{}".format(
            handler_input.request_envelope.request))


class SaveDataInterceptor(AbstractResponseInterceptor):
    """Save persistence attributes before sending response to user."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes

        persistent_attributes["past_celebs"] = session_attributes["past_celebs"] if CELEB_TRACKING  else []
        persistent_attributes["visits"] = session_attributes["visits"]

        handler_input.attributes_manager.save_persistent_attributes()

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug('----- RESPONSE -----')
        logger.debug("{}".format(response))
        
  #new class to open skill      
class APLEventHandler (AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("Alexa.Presentation.APL.UserEvent")(handler_input)

    def handle(self, handler_input):
        logger.info("in APLEventHandler")
        eventType = handler_input.request_envelope.request.arguments[0]
        should_end_session = False 
        speak_output = ""
        logger.info(eventType)
        if eventType =='openSkill': 
            # If the user taps on header, launch the skill.
            return LaunchRequestHandler.handle(self, handler_input)
            
        return (
            handler_input.response_builder
                .set_should_end_session(should_end_session)
                .add_directive(
                        RenderDocumentDirective(
                            token="pagerToken",
                            document = _load_apl_document(launchDocument),
                            datasources=_load_apl_document(datasourceDocument)
                        )
                    )
                .response
        )



# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = StandardSkillBuilder(
    table_name=os.environ.get("DYNAMODB_PERSISTENCE_TABLE_NAME"), auto_create_table=False)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PlayGameHandler())
sb.add_request_handler(GetBirthdayIntentHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

# Interceptors
sb.add_global_request_interceptor(LoadDataInterceptor())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

sb.add_global_response_interceptor(SaveDataInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()