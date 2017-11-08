"""This is a template for State Machine Modules

   A State Machine module is a python file that contains a  `loop` function.
   Similar to how an Arduino program operates, `loop` is called continuously:
   when the function terminates, it is called again.

   The `loop` function should continuously listens to messages generated by:
   - the path detector (concerning the path to follow),
   - the sign detector (concerning road signs detected, if any),
   - the remote command operator (concerning commands to start/stop driving,
     or do specific manoeuvers)
   - and the arduino controller of the physical car (concerning the current
     state; possible sensor readings, ...)

   and decide on how to drive the car correspondingly. See the description of
   the `loop` method below for more details.
"""
#testing
import logging
import time
from event import Event
from car import Car


class InnerState : 
    IN = 1
    DONE = 0


class CarState : 
    # constants for the different states in which we can be operating
    IDLE = 1
    STOPPED = 2
    MOVING = 3 
    # You can add other states here


# Setup up the state machine. The following code is called when the state
# machine is loaded for the first time.
logging.info('Template StateMachine has been initialized')

# The next variable is a global variable used to store the state between
# successive calls to loop()
state = CarState.IDLE
MainAction = None 
SubMovement = None 

def StartTimer(interval) : 
    time_at_the_beginning = time.time()
    time_difference = ( time_at_the_beginning + interval) - time.time()
    while ( time_difference > 0 ) : 
        yield InnerState.IN
        time_difference = ( time_at_the_beginning + interval) - time.time()
    yield InnerState.DONE

def Stop_Car() : 
    global state
    global SubMovement
    SubMovement = None 
    state = CarState.STOPPED 
    Car.send(0, 0, 0, 0) 
    logging.info( "you just stopped the car, here is the current state " +  str(state) ) 



################# subfunctions ( movement ) ################################## 

def Rotate(angle) : 
    Car.send(0, 0, 0.05, angle) 
    time.sleep(0.01) 
    Car.send(0, 0, 0, 0) 
    yield InnerState.DONE

def GoForth( time_interval, speed ) : 
    timer = StartTimer( time_interval ) 
    Car.send( 0, 0, speed, 0.)
    while ( next(timer) != 0 ) : 
        yield InnerState.IN
    yield InnerState.DONE


def Turn( angle, radius, speed  ) : 
    ratio_angelOfRotation_Radius = 5       #gotta determine by trial and error
    distance = angle * radius 
    time_to_make_rotation = speed * distance  

    timer = StartTimer(time_to_make_rotation)

    Car.send( 0, 0, speed, ratio_angelOfRotation_Radius * radius)
    while (next( timer ) != InnerState.DONE ) : 
        yield InnerState.IN
    yield InnerState.DONE
    
    
    
##############################################################################

###################### Main Action ###########################################

def Square(side_length , speed ) : 
    for i in range(4) : 
        yield GoForth(side_length / speed , speed)
        yield Rotate(90) 
    Stop_Car()
    yield None

def Spiral() : 
   logging.info( "spiral being called " ) 
   index = 0
   while index < 7200 : 
       yield Rotate( index ) 
       index += 1 
   Stop_Car()
   yield None

def ForhtMainAction (interval) : 
    yield GoForth(interval) 
    Stop_Car()
    yield None 

##################################################################################

def loop():
    '''State machine control loop.
    Like an arduino program, this function is called repeatedly: whenever
    it exits it is called again. Inside the function, call:
    - time.sleep(x) to sleep for x seconds (x can be fractional)
    - Event.poll() to get the next event (output of Path and/or Sign detector,
      status sent by the car, or remote command).
    - Car.send(x,y,u,v) to communicate two integers (x and y) and
      two floats(u,v) to the car. How the car interprets this message depends
      on how you implement the arduino nano. For the simulator, x, and y
      are ignored while u encodes the speed and v the relative angle to turn
      to.
    '''
    global state  # define state to be a global variable
    global SubMovement
    global MainAction
    event = Event.poll()
    if event is not None:        # only if there is some change ( instantiate action ) #me
        if event.type == Event.CMD and event.val == "GO":
            logging.info( " Up and running, boss !" ) 
        elif event.type == Event.CMD and event.val == "SPIRAL" : 
            MainAction = Spiral() 
            state = CarState.MOVING
        elif event.type == Event.CMD and event.val == "FORTH":
            MainAction = ForhtMainAction(3) 
            state = CarState.MOVING
        elif event.type == Event.CMD and event.val == "SQUARE": 
            MainAction = Square(1, 90)
            state = CarState.MOVING
        elif event.type == Event.CMD and event.val == "STOP":
            Car_Stop()


        elif event.type == Event.PATH:
            # You received the PATH dictionary emitted by the path detector
            # you can access this dictionary in event.val
            # actuate car coresspondingly, change state if relevant
            pass
        elif event.type == Event.SIGN:
            # You received the SIGN dictionary emitted by the sign detector
            # you can access this dictionary in event.val
            # actuate car coresspondingly, change state if relevant
            pass
        elif event.type == Event.CAR:
            # You received a message from the arduino that is operating the car
            # In this case, event.val contains a dictionary with keys x,y,u,v
            # where x and y are ints; u,v, are floats.
            # Act on this message depending on how you implemented the arduino
            # (e.g., is the arduino sending that there is an obstacle in front
            # and you should stop ?)
            logging.info("Received CAR event with x=%d, y=%d, u=%f, v=%f" %
                (event.val['x'], event.val['y'], event.val['u'], event.val['v']))
            pass
    else : 
        if not (state ==  CarState.IDLE or state == CarState.STOPPED) : 
            if SubMovement == None or next( SubMovement ) == InnerState.DONE:        # next has to come after !!!!!!! 
                SubMovement = next(MainAction) 
              