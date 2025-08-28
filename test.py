import tensorflow as tf, tensorflow_hub as hub  

print("TensorFlow version:", tf.__version__)
print("TensorFlow Hub version:", hub.__version__)

url = "https://www.kaggle.com/models/google/bird-vocalization-classifier/frameworks/TensorFlow2/variations/perch_v2_cpu/versions/1"  
m = hub.load(url)  
f = m.signatures.get("serving_default", next(iter(m.signatures.values())))  
inp = list(f.structured_input_signature[1].keys())[0]  
out = f(**{inp: tf.zeros([1,160000], tf.float32)})  
print("OK", {k: v.shape for k,v in out.items()})