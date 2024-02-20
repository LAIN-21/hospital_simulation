import simpy
import random
import numpy as np
import csv
from statistics import mean
import pandas as pd
random.seed(2023)

# Second Part: First generator function
def patient_generator(env, avg_arrival, avg_consultation,avg_book_surgery,receptionist,doctor):
  patient_id = 1

  while True:
    p = activity_generator_patient(env,avg_registration,avg_consultation,avg_book_surgery,receptionist,doctor,patient_id)
    env.process(p)
    t = random.expovariate(1/avg_arrival)

    yield env.timeout(t)
    patient_id += 1

# Second Part: Second Generator Function
def caller_generator(env, avg_calling, avg_answering_call, receptionist):
  caller_id = 1

  while True:
    p = activity_generator_caller(env, avg_calling, avg_answering_call, receptionist, caller_id)
    env.process(p)
    t = random.expovariate(1/avg_calling)

    yield env.timeout(t)
    caller_id += 1

# Third Part: First Activity Function
def activity_generator_patient(env,avg_registration,avg_consultation,avg_book_surgery,receptionist,doctor,patient_id):

  global queuing_times_receptionist_list
  global queuing_times_consultation_list
  global queuing_times_surgery_booking_list
  global total_time_in_system1_list

  time_entered_queue_registration = env.now

  with receptionist.request() as req:
    yield req

    time_left_queue_registration = env.now
    time_in_queue_registration = time_left_queue_registration - time_entered_queue_registration
    print (" \\(o-o)/ Patient %s queued for registration for %.2f minutes" % (patient_id, time_in_queue_registration))

    if env.now > warm_up_period:
      queuing_times_receptionist_list.append(time_in_queue_registration)

    registration_time = random.expovariate(1/avg_registration)
    yield env.timeout(registration_time)

  time_entered_queue_consultation = env.now

  with doctor.request() as req:
    yield req

    time_left_queue_consultation = env.now
    time_in_queue_consultation = time_left_queue_consultation - time_entered_queue_consultation
    print (" \\(o-o)/ Patient %s queued for consultation for %.2f minutes" % (patient_id, time_in_queue_consultation))

    if env.now > warm_up_period:
      queuing_times_consultation_list.append(time_in_queue_consultation)

    consultation_time = random.expovariate(1/avg_consultation)
    yield env.timeout(consultation_time)

  decide_surgery = random.uniform(0,1)

  if decide_surgery < 0.25:
    time_entered_surgery_booking_queue = env.now
    with receptionist.request() as req:
      yield req

      time_left_surgery_booking_queue = env.now
      time_in_surgery_booking_queue = time_left_surgery_booking_queue - time_entered_surgery_booking_queue
      print (" \\(o-o)/ Patient %s queued for surgery booking for %.2f minutes" % (patient_id, time_in_surgery_booking_queue))

      if env.now > warm_up_period:
        queuing_times_surgery_booking_list.append(time_in_surgery_booking_queue)

      #Total Time if Went to Surgery Booking
      total_time_with_booking = time_left_surgery_booking_queue - time_entered_queue_registration
      total_time_in_system1_list.append(total_time_with_booking)

      surgery_booking_time = random.expovariate(1/avg_book_surgery)
      yield env.timeout(surgery_booking_time)
  else:
    time_left = env.now
    print(f'Patient {patient_id} left the office at {time_left}')

    #Total Time if not Went to Surgery Booking
    Total_without_booking = time_left - time_entered_queue_registration

    if env.now > warm_up_period:
      total_time_in_system1_list.append(Total_without_booking)

# Third Part: Second Activity Function
def activity_generator_caller(env, avg_calling, avg_answering_call, receptionist, caller_id):

  global queuing_times_calling_list
  global total_time_in_system2_list

  time_entered_calling_queue = env.now

  with receptionist.request() as req:
    yield req

    time_left_calling_queue = env.now
    time_in_calling_queue = time_left_calling_queue - time_entered_calling_queue
    print (" \\(o-o)/ Caller %s queued for calling for %.2f minutes" % (caller_id, time_in_calling_queue))

    if env.now > warm_up_period:
      queuing_times_calling_list.append(time_in_calling_queue)

    call_time = random.expovariate(1/avg_calling)
    yield env.timeout(call_time)

    final_time = env.now
    total_system_time = final_time - time_entered_calling_queue

    if env.now > warm_up_period:
      total_time_in_system2_list.append(total_system_time)


n_runs = 100

with open('results.csv', 'w', newline='') as file:
  writer = csv.writer(file)
  writer.writerow(['Run', 'Mean Queuing Time Receptionist', 'Mean Queuing Time Consultation', 'Mean Queuing Time Surgery Booking', 'Mean Total Time in System 1', 'Mean Queuing Time Calling', 'Mean Total Time in System 2'])
  
for run in range(n_runs):
  #Variables and Running
  env = simpy.Environment()
  receptionist = simpy.Resource(env, capacity = 1)
  doctor = simpy.Resource(env, capacity = 2)

  # For Activity 1

  avg_arrival = 3
  avg_registration = 2
  avg_consultation = 8
  avg_book_surgery = 4

  queuing_times_receptionist_list = []
  queuing_times_consultation_list = []
  queuing_times_surgery_booking_list = []
  total_time_in_system1_list = []

  # For Activity 2

  avg_calling = 10
  avg_answering_call = 4

  queuing_times_calling_list = []
  total_time_in_system2_list = []

  # Running Settings
  warm_up_period = 180
  running_collection_period = 480
  total_running_period = warm_up_period + running_collection_period

  env.process(patient_generator(env, avg_arrival, avg_consultation,avg_book_surgery,receptionist,doctor))
  env.process(caller_generator(env, avg_calling, avg_answering_call, receptionist))

  env.run(until=total_running_period)

  # Calculating the Mean of the Lists
  mean_queuing_time_receptionist = mean(queuing_times_receptionist_list)
  mean_queuing_time_consultation = mean(queuing_times_consultation_list)
  mean_queuing_time_surgery_booking = mean(queuing_times_surgery_booking_list)
  mean_total_time_in_system1 = mean(total_time_in_system1_list)
  mean_queuing_time_calling = mean(queuing_times_calling_list)
  mean_total_time_in_system2 = mean(total_time_in_system2_list)

  # Writing the Results
  list_results = [run, mean_queuing_time_receptionist, mean_queuing_time_consultation, mean_queuing_time_surgery_booking, mean_total_time_in_system1, mean_queuing_time_calling, mean_total_time_in_system2]
  with open('results.csv', 'a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(list_results)
  
# Reading the Results
df = pd.read_csv('results.csv')
average_mean_queuing_time_receptionist = df['Mean Queuing Time Receptionist'].mean()
average_mean_queuing_time_consultation = df['Mean Queuing Time Consultation'].mean()
average_mean_queuing_time_surgery_booking = df['Mean Queuing Time Surgery Booking'].mean()
average_mean_total_time_in_system1 = df['Mean Total Time in System 1'].mean()
average_mean_queuing_time_calling = df['Mean Queuing Time Calling'].mean()
average_mean_total_time_in_system2 = df['Mean Total Time in System 2'].mean()

print(f'Average Mean Queuing Time Receptionist: {average_mean_queuing_time_receptionist}')
print(f'Average Mean Queuing Time Consultation: {average_mean_queuing_time_consultation}')
print(f'Average Mean Queuing Time Surgery Booking: {average_mean_queuing_time_surgery_booking}')
print(f'Average Mean Total Time in System 1: {average_mean_total_time_in_system1}')
print(f'Average Mean Queuing Time Calling: {average_mean_queuing_time_calling}')
print(f'Average Mean Total Time in System 2: {average_mean_total_time_in_system2}')

# End of the code

