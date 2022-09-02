import xml.etree.ElementTree as xml
import time
import os
import datetime
from datetime import date

def GetXML(sprav, fsrar):
	# Создание XML-файла запроса марок по B-справке
	Version = "1.0"
	HTML_NS  =  "http://www.w3.org/2001/XMLSchema-instance"
	XSL_NS   =  "http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
	HTM_NS   =  "http://fsrar.ru/WEGAIS/QueryParameters"
	NS_MAP = { 'Version': Version,
	  'xmlns:xsi':  HTML_NS,
	  "xmlns:ns": XSL_NS,
	  "xmlns:qp": HTM_NS
	   }

	root = xml.Element('ns:Documents', NS_MAP)

	appt = xml.Element("ns:Owner")
	root.append(appt)

	fsrar_id = xml.SubElement(appt, "ns:FSRAR_ID")
	fsrar_id.text = fsrar

	doc = xml.Element("ns:Document")
	root.append(doc)

	doc_type = xml.SubElement(doc, "ns:QueryRestBCode")

	params = xml.SubElement(doc_type, "qp:Parameters")

	param = xml.SubElement(params, "qp:Parameter")

	name = xml.SubElement(param, "qp:Name")
	name.text = "ФОРМА2"

	val = xml.SubElement(param, "qp:Value")
	val.text = sprav

	tree = xml.ElementTree(root)
	with open("GetMarkFB2.xml", "wb") as fh:
		tree.write(fh, xml_declaration='True', encoding='UTF-8')

def WriteXML(num_act, fsrar):
	# Парсим ответ от ФСРАР + содзаём документ списания
	Version = "1.0"
	XSI_NS  =  "http://www.w3.org/2001/XMLSchema-instance"
	NS_NS   =  "http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
	PREF_NS   =  "http://fsrar.ru/WEGAIS/ProductRef_v2"
	AWR_NS = "http://fsrar.ru/WEGAIS/ActWriteOff_v3"
	CE_NS = "http://fsrar.ru/WEGAIS/CommonV3"
	NS_MAP = { 'Version': Version,
	  'xmlns:xsi':  XSI_NS,
	  "xmlns:ns": NS_NS,
	  "xmlns:pref": PREF_NS,
	  "xmlns:awr": AWR_NS,
	  "xmlns:ce": CE_NS
	   }

	tree = xml.parse("ReplyRestBCode.xml")
	node = tree.getroot()

	root = xml.Element('ns:Documents', NS_MAP)

	appt = xml.Element("ns:Owner")
	root.append(appt)

	fsrar_id = xml.SubElement(appt, "ns:FSRAR_ID")
	fsrar_id.text = fsrar

	doc = xml.Element("ns:Document")
	root.append(doc)

	doc_type = xml.SubElement(doc, "ns:ActWriteOff_v3")

	awr_ident = xml.SubElement(doc_type, "awr:Identity")
	awr_ident.text = "456"

	awr_header = xml.SubElement(doc_type, "awr:Header")

	# Номер акта
	awr_actnum = xml.SubElement(awr_header, "awr:ActNumber")
	awr_actnum.text = str(num_act)

	# Дата проведения акта
	awr_actdate = xml.SubElement(awr_header, "awr:ActDate")
	awr_actdate.text = str(date.today())

	awr_type = xml.SubElement(awr_header, "awr:TypeWriteOff")
	awr_type.text = "Потери"

	awr_note = xml.SubElement(awr_header, "awr:Note")
	awr_note.text = " "

	awr_content = xml.SubElement(doc_type, "awr:Content")

	awr_position = xml.SubElement(awr_content, "awr:Position")

	awr_ident = xml.SubElement(awr_position, "awr:Identity")
	awr_ident.text = "1"

	kol = 0
	for el in node[1][0]:
		kol = kol + 1

	if kol < 3 :
		print("Нету марок. Нечего отправлять.")
		return 0
	else:
		# Вытаскиваем марки + подсчитываем их количество
		kol = 0
		for item in node[1][0][2]:
			kol = kol + 1

		awr_quant = xml.SubElement(awr_position, "awr:Quantity")
		awr_quant.text = str(kol)

		awr_inf12 = xml.SubElement(awr_position, "awr:InformF1F2")

		awr_inf2 = xml.SubElement(awr_inf12, "awr:InformF2")

		pref_f2 = xml.SubElement(awr_inf2, "pref:F2RegId")
		pref_f2.text = node[1][0][1].text

		marks = xml.SubElement(awr_position, "awr:MarkCodeInfo")
		for item in node[1][0][2]:
			ce_amc = xml.SubElement(marks, "ce:amc")
			ce_amc.text = item.text

		tree = xml.ElementTree(root)
		with open("ActWriteOff_v3.xml", "wb") as fh:
			tree.write(fh, xml_declaration='True', encoding='UTF-8')
		return 1

fsrar_num = input("Введите FSRAR_ID: ")
ip = input("Введите ip УТМ ввиде 192.168.255.250: ")
# fsrar_num = "030000438581"
# ip = "10.114.40.11"
ip = "http://" + ip + ":8080"

f = open('ost.csv', 'r')

# Номер акта
index = int(input("Введите начальный номер акта: "));

for item in f.read().split("\n"):
	print("----------------Новая итерация----------------")
	print(datetime.datetime.now())
	print("Код итерации: ", index)
	print("Код товара: ", item.split(";")[3])
	print("Наименование товара: ", item.split(";")[4])
	print("Справка: ", item.split(";")[6])
	
	if index == 1:
		GetXML(item.split(";")[6], fsrar_num)
		index = index + 1;
	
		# Делаем запрос марок по справке B
		print("Отправляем запрос марок по 2ой справке:")
		st = "curl -F''xml_file=@GetMarkFB2.xml'' " + ip + "/opt/in/QueryRestBCode > getref.xml"
		os.system(st)
		print(st)

		print("Ждём 11 минут...")
		time.sleep(660)
	elif index > 1:
		# Парсим ссылку на ответ
		tree = xml.parse("getref.xml")
		node = tree.getroot()
		print("Парсим ссылку на ответ на запрос марок предыдущей итерации:")
		st = "curl -X GET " + ip +"/opt/out?replyId=" + node[0].text + " > getref2.xml"
		os.system(st)
		print(st)

		# Получаем ответ
		print("Получаем ответ:")
		tree = xml.parse("getref2.xml")
		node = tree.getroot()
		if node[0].text != "1":
			st = "curl -X GET " + node[0].text + " > ReplyRestBCode.xml"
			os.system(st)
			print(st)

		ch = WriteXML(index, fsrar_num)

		GetXML(item.split(";")[6], fsrar_num)
		index = index + 1;

		# Делаем запрос марок по справке B
		print("Отправляем запрос марок по 2ой справке:")
		st = "curl -F''xml_file=@GetMarkFB2.xml'' " + ip + "/opt/in/QueryRestBCode > getref.xml"
		os.system(st)
		print(st)

		if ch == 0:
			print("Ждём 11 минут...")
			time.sleep(660)
			continue
		else:
			# Отправляем запрос на списание марок из предыдущей итерации
			print("Отправляем запрос на списание:")
			st = "curl -F''xml_file=@ActWriteOff_v3.xml'' " + ip + "/opt/in/ActWriteOff_v3 > getwr.xml"
			os.system(st)
			print(st)

			print("Ждём 11 минут...")
			time.sleep(660)

			# Парсим ссылку на ответ
			tree = xml.parse("getwr.xml")
			node = tree.getroot()
			print("Парсим ссылку на ответ на запрос марок предыдущей итерации:")
			st = "curl -X GET " + ip +"/opt/out?replyId=" + node[0].text + " > getwr2.xml"
			os.system(st)
			print(st)
					
			# Получаем ответ
			print("Получаем ответ:")
			tree = xml.parse("getwr2.xml")
			node = tree.getroot()
			
			kol = 0;
			for elem in node:
				kol = kol + 1

			if kol > 2:
				st1 = "curl -X GET " + node[0].text + " > TicketA.xml"
				st2 = "curl -X GET " + node[1].text + " > TicketB.xml"

				os.system(st1)
				os.system(st2)
			elif kol == 2:
				st1 = "curl -X GET " + node[0].text + " >> " + item.split(";")[3] + ".err"
				os.system(st1)