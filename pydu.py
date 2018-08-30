from struct import *
import time 
import os 
from os import path 
import mmap 

# print("Welcome to PyDU, the Python-based Dialog Utility")
'''
class GameData(): 

	def __init__(self,key):
		self.data = read_key(key) 

	def get_resource_raw(self,resource):
		return self.data.get(resource.upper())
'''

class Resource: 
	# name, type, location, size 
	# read/write for byte, short, long, res, string (32)

	def __init__(self,resource):
		# resource is a string: [name].[ext]
		ressplit = resource.split('.')
		self.resource = resource
		self.resref = ressplit[0]
		self.ext = ressplit[1]
		self.file = get(resource)
		self.size = os.path.getsize(self.file)

	def delete_override(self):
		os.remove(self.file)

	# call this only at the end of an install/component
	def delete_unchanged(self):
		with open(self.file,'rb') as f:
			override_data = f.read(self.size)
			base_data = keydata.get((self.resource).upper())
			if override_data == base_data: 
				unchanged = True 
		if unchanged: 
			self.delete_override()

	def copy_as(self,name):
		with open(self.file,'rb') as f:
			data = f.read(self.size)
			file = open(path.join(path.abspath(path.dirname(__file__)),'override',name),'wb')
			file.write(data)
			file.close()


	def read_ascii(self,offset,length=8):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			return f.read(length).decode('ascii')

	def write_ascii(self,offset,value,length=8):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack(str(length)+'s',value.encode('ascii')))
			f.close()

	def read_byte(self,offset,signed=False):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			if signed:
				return unpack('b',f.read(1))[0]
			else: 
				return unpack('B',f.read(1))[0]

	def write_byte(self,offset,value):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack('B',value))
			f.close()

	def read_short(self,offset,signed=False):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			if signed:
				return unpack('h',f.read(2))[0]
			else:
				return unpack('H',f.read(2))[0]

	def write_short(self,offset,value):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack('H',value))
			f.close()

	def read_long(self,offset,signed=False):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			if signed:
				return unpack('l',f.read(4))[0]
			else:
				return unpack('L',f.read(4))[0]

	def write_long(self,offset,value):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack('L',value))
			f.close()
			
def read_key(key):
	with open(key,"r+b") as f:
		# HEADER
		sigver = f.read(8).decode('ascii')
		if sigver != 'KEY V1  ':
			raise ValueError('Invalid KEY signature')
		f.seek(8)
		bifcount = unpack('L',f.read(4))[0]
		f.seek(12)
		rescount = unpack('L',f.read(4))[0]
		f.seek(16)
		bifoff = unpack('L',f.read(4))[0]
		f.seek(20)
		resoff = unpack('L',f.read(4))[0]
		#print(bifcount, rescount, bifoff, resoff)

		# resources
		keyresources = list()
		for i in range(0,rescount):
			f.seek(resoff + 14 * i)
			resname = unpack('8s',f.read(8))[0].decode('ascii')
			f.seek(resoff + 14 * i + 8)
			restype = unpack('H',f.read(2))[0] 
			f.seek(resoff + 14 * i + 10)
			reslocator = unpack('L',f.read(4))[0]
			bifindex = reslocator>>20
			reslocator_nobif = reslocator - (bifindex << 20)
			if reslocator_nobif >> 14:
				resindex = reslocator_nobif >> 14 
			else:
				resindex = reslocator_nobif
			keyresources.append((resname,restype,bifindex,resindex))
			#print(resname,restype,bifindex,resindex)

		# bifs 
		keybifs = list()
		bif_indices = dict()
		for i in range(0,bifcount):
			f.seek(bifoff + 12 * i)
			biflength = unpack('L',f.read(4))[0]
			f.seek(bifoff + 12 * i + 4)
			bifnameoff = unpack('L',f.read(4))[0]
			f.seek(bifoff + 12 * i + 8)
			bifnamelength = unpack('H',f.read(2))[0]
			f.seek(bifoff + 12 * i + 10)
			biflocflag = unpack('H',f.read(2))[0]
			f.seek(bifnameoff)
			bifname = unpack(str(bifnamelength-1)+'s',f.read(bifnamelength-1))[0].decode('ascii')
			#print(type(bifname))
			keybifs.append((bifname,i,biflength,biflocflag))
			bif_indices[i] = bifname
			# print(bifname, i, biflength,biflocflag)

		key_data = dict()
		# key_data[bifindex][resindex] returns the unpacked byte code of the resource numbered resindex in the the bif numbered bifindex

		for bif in keybifs: 
			key_data[bif[1]] = read_bif(bif[0])
		#print(key_data)

		res_data = dict()
		for res in keyresources:
			resname = res[0]
			restype = res[1]
			bifindex = res[2]
			resindex = res[3] 
			if restype == 0x3f1: #creature 
				filename = resname.rstrip('\x00').upper()+'.CRE'
				res_data[filename] = key_data[bifindex][resindex]

	return res_data 
	#print(resname,restype,bif_indices[bifindex])
	#print(resname,restype)

def read_bif(bif):
	# bif is the bif file (with .bif extension)
	with open(bif,"r+b") as f:
		#print(type(bif))
		# HEADER
		sigver = f.read(8).decode('ascii')
		if sigver != 'BIFFV1  ':
			raise ValueError('Invalid decompressed BIFF signature')
		f.seek(8)
		filecount = unpack('L',f.read(4))[0]
		f.seek(12)
		tsetcount = unpack('L',f.read(4))[0]
		f.seek(16)
		entryoff = unpack('L',f.read(4))[0]

		resources = list()
		key_resources = dict()
		# resources
		for i in range(0,filecount):
			f.seek(entryoff)
			reslocator = unpack('L',f.read(4))[0]
			f.seek(entryoff + 4)
			resoff = unpack('L',f.read(4))[0]
			f.seek(entryoff + 8)
			ressize = unpack('L',f.read(4))[0]
			f.seek(entryoff + 12)
			restype = unpack('H',f.read(2))[0]
			resources.append((reslocator,resoff,ressize,restype))
			f.seek(resoff)
			#key_resources[reslocator] = pack(str(ressize)+'s',f.read(ressize))
			#key_resources[reslocator] = repr(unpack(str(ressize)+'s',f.read(ressize))[0])
			key_resources[reslocator] = f.read(ressize)
			#print((reslocator,resoff,ressize,restype))
			entryoff = entryoff + 16
		

		tilesets = list()
		# tilesets 
		for i in range(0,tsetcount):
			f.seek(entryoff)
			reslocator = unpack('L',f.read(4))[0]
			f.seek(entryoff + 4)
			resoff = unpack('L',f.read(4))[0]
			f.seek(entryoff + 8)
			tilecount = unpack('L',f.read(4))[0]
			f.seek(entryoff + 12)
			tilesize = unpack('L',f.read(4))[0]
			f.seek(entryoff + 16)
			restype = unpack('H',f.read(2))[0]
			tilesets.append((reslocator,resoff,tilecount,tilesize,restype))
			#f.seek(resoff)
			#key_resources[reslocator] = f.read(ressize)
			entryoff = entryoff + 20

		return key_resources

		# do stuff with resources/tilesets here
		'''for resource in resources:
			f.seek(resource[1] + 716)
			dialog = unpack('8s',f.read(8))[0].decode('utf-8')
		'''
		#print(dialog)
	#print("Loaded:",bif)

#t = time.time()
#data = read_key('chitin.key')
def save_to_override(name,data):
	file = open(path.join(path.abspath(path.dirname(__file__)),'override',name),'wb')
	file.write(data)
	file.close()

def get_resource_raw(resource):
	# this returns the bytes making up the desired resource (as found in keydata)
	return keydata.get(resource.upper())

def get_resource_parsed(resource):
	pass

def get(resource):
	# input resref.xyz
	# output filename of resref.xyz in override
	if path.isfile('./override/'+resource):
		#print('File in override')
		file = path.join(path.abspath(path.dirname(__file__)),'override',resource)
	elif keydata.get(resource.upper()):
		#print('File in game files')
		data = keydata.get(resource.upper())
		save_to_override(resource,data)
		file = path.join(path.abspath(path.dirname(__file__)),'override',resource)
	else:
		#print('File not found')
		file = None
	#data = get_resource_raw(resource) 
	return file



if __name__ == '__main__':

	t = time.time()
	global keydata 
	keydata = read_key('chitin.key')

	Accalia = Resource('Accalia.cre')
	print(Accalia.resref,Accalia.ext,Accalia.file,Accalia.size)
	print(Accalia.read_ascii(0x2cc))
	#print(Accalia.resref,Accalia.ext,Accalia.file,Accalia.size)
	print(Accalia.write_ascii(0x2cc,'ANDREWWWW'))
	#Accalia.delete_unchanged()
	#print(Accalia.resref,Accalia.ext,Accalia.file,Accalia.size)
	print(Accalia.read_ascii(0x2cc))
	print(Accalia.read_byte(0x2c))
	Accalia.write_byte(0x2c,155)
	print(Accalia.read_byte(0x2c))
	Accalia.copy_as('Accalia2.cre')

	Accalia2 =
	# Accalia.delete_override()
	print(type(Accalia))
