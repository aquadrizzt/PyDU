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
		self.resref = ressplit[0]
		self.ext = ressplit[1]
		self.file = get(resource)
		self.size = os.path.getsize(self.file)

	def read_resref(self,offset):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			return f.read(8).decode('utf-8')

	def write_resref(self,offset,value):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack('8s',value.encode('utf-8')))
			f.close()

	def read_byte(self,offset):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'rb') as f:
			f.seek(offset)
			return unpack('B',f.read(1))[0]

	def write_byte(self,offset,value):
		# offset is a number (in decimal or 0x.. format)
		with open(self.file,'r+b') as f:
			f.seek(offset)
			f.write(pack('B',value))
			f.close()
			
def read_key(key):
	with open(key,"r+b") as f:
		# HEADER
		sigver = f.read(8).decode('utf-8')
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
			resname = unpack('8s',f.read(8))[0].decode('utf-8')
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
			bifname = unpack(str(bifnamelength-1)+'s',f.read(bifnamelength-1))[0].decode('utf-8')
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
		sigver = f.read(8).decode('utf-8')
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
	print(Accalia.read_resref(0x2cc))
	#print(Accalia.resref,Accalia.ext,Accalia.file,Accalia.size)
	print(Accalia.write_resref(0x2cc,'andrewwwwww'))
	#print(Accalia.resref,Accalia.ext,Accalia.file,Accalia.size)
	print(Accalia.read_resref(0x2cc))
	print(Accalia.read_byte(0x2c))
	Accalia.write_byte(0x2c,155)
	print(Accalia.read_byte(0x2c))

	'''
	get('ad3sklm.cre')
	get('andrew.cre')

	print(time.time()-t)

	with open(res,"r+b") as f:
		sigver = f.read(8).decode('utf-8')
		print(sigver)
		f.seek(0x2cc)
		f.write(pack('8s','andrew'.encode('utf-8')))
		f.seek(0x2cc)
		print(unpack('8s',f.read(8))[0].decode('utf-8'))
	'''

'''
print(res)
with open(res,'rb') as f:
	print(type(f))
	f.seek(24)
	tilesize = unpack('L',f.read(4))[0]
	print(tilesize)
'''
#print(accalia.decode('ascii'))

# save_to_override('accalia.cre',accalia)
#print(time.time() - t)

# goals 
## perform functions similar to weidu, but within python 
## allow for extension into a user interface like NI that can generate weidu code from changes
