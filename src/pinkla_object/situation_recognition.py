from pinkla_object.predict_distance import Find_Object
import xml.etree.ElementTree as ET

class Situation_Recognition():
    def __init__(self):
        self.xml_path = "../pinkla_object/situation_control.xml" 

    def find_scenario(self, objects_status):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        matching_descriptions = []

        # detect된 객체만을 포함하는 search_criteria 생성
        detect_objects = [obj for obj, status in objects_status.items() if status == 'detect']
        undetect_objects = [obj for obj, status in objects_status.items() if status != 'detect']

        if detect_objects:
            # detect된 객체만을 포함하는 search_criteria 생성
            search_criteria = detect_objects

            # # situation 태그를 순회하며 검색

            for situation in root.findall('situation'):
                description = situation.find('description').text

                # 상황 설명에서 detect된 객체의 단어만을 고려하여 일치 여부 확인
                matches = all(obj in description for obj in search_criteria)
                
                # detect된 객체가 포함되어 있고, undetect된 객체가 포함되어 있지 않은 경우에만 추가
                if matches and not any(obj in description for obj in undetect_objects):
                    matching_descriptions.append(description)

        return matching_descriptions

    def only_name_distance(self, obj_result):
        object_info_list = []

        for obj_info in obj_result:
            class_name = obj_info[0]
            distance = obj_info[2]  # distance가 2번째 index에 위치함
            object_info_list.append([class_name, distance])

        return object_info_list

    def recognition(self, detected_objects):
        objects_status = {
            "car": None,
            "crosswalk": None,
            "green_light": None,
            "human": None,
            "only_right_turn": None,
            "only_straight": None,
            "red_light": None,
            "start_line": None,
            "stop_line": None,
            "yellow_light": None
        }

        for class_name, distance in detected_objects:
            if class_name == "car" and distance < 15.0:
                objects_status["car"] = "detect"
            elif class_name == "crosswalk" and distance < 25.0:
                objects_status["crosswalk"] = "detect"
            elif class_name == "green_light" and distance < 80.0:
                objects_status["green_light"] = "detect"
            elif class_name == "human" and distance < 25.0:
                objects_status["human"] = "detect"
            elif class_name == "only_right_turn" and distance < 80.0:
                objects_status["only_right_turn"] = "detect"
            elif class_name == "only_straight" and distance < 80.0:
                objects_status["only_straight"] = "detect"
            elif class_name == "red_light" and distance < 80.0:
                objects_status["red_light"] = "detect"
            elif class_name == "start_line" and distance < 20.0:
                objects_status["start_line"] = "detect"
            elif class_name == "stop_line" and distance < 25.0:
                objects_status["stop_line"] = "detect"      
            elif class_name == "yellow_light" and distance < 80.0:
                objects_status["yellow_light"] = "detect"                                           
                        

        return objects_status
