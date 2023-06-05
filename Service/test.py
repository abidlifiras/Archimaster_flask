import json
import Scoring as scoring

(jsonStrategie,image_path_strategie)=scoring.calculate_scores(152,2)

key = list(jsonStrategie.keys())[0]
value = list(jsonStrategie.values())[0]
print((key,value))