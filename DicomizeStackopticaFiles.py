# Stackoptica - 3D Viewer on calibrated images - Orthanc Plugin

# Copyright (C) 2024 Yann Pollet, Royal Belgian Institute of Natural Sciences

#

# This program is free software: you can redistribute it and/or

# modify it under the terms of the GNU Affero General Public License

# as published by the Free Software Foundation, either version 3 of

# the License, or (at your option) any later version.

# 

# This program is distributed in the hope that it will be useful, but

# WITHOUT ANY WARRANTY; without even the implied warranty of

# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU

# Affero General Public License for more details.

#

# You should have received a copy of the GNU Affero General Public License

# along with this program. If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO
import PIL
import datetime
import pydicom
from pydicom.valuerep import VR
import glob
import json
import requests
import os

path_to_project = "data/microscope"
SOURCE = f'{path_to_project}/*.jpg'
calib_file = f'{path_to_project}/stack.json'
images = sorted(glob.glob(SOURCE))
i = 0


with open(calib_file, 'rb') as f:
    stack_dict = json.load(f)
    
study_uid = pydicom.uid.generate_uid()
series_uid = pydicom.uid.generate_uid()


thumbnails_width = stack_dict["thumbnails_width"]
thumbnails_height  = stack_dict["thumbnails_height"]

images = stack_dict["stack"]
stacked_images = stack_dict["Stacked_images"]

now = datetime.datetime.now()

for image_name in images:
    image_data = images[image_name]
    image = f"{path_to_project}/{image_name}"
    camera = os.path.basename(image)
    print(camera)
    ds = pydicom.dataset.Dataset()
    ds.PatientName = 'Periglischrus^calcariflexus'
    ds.PatientID = 'Periglischrus10275665'
    ds.PatientBirthDate = '20200914'
    ds.PatientSex = 'O'

    
    ds.StudyDate = now.strftime('%Y%m%d')
    ds.StudyTime = now.strftime('%H%M%S')

    ds.ImageType = [ 'ORIGINAL', 'PRIMARY' ]
    ds.UserContentLabel = camera
    ds.Laterality = 'L'
    ds.LossyImageCompression = '01'
    ds.Modality = 'XC'  # External-camera photography
    ds.SOPClassUID = pydicom.uid.VLPhotographicImageStorage
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = study_uid
    ds.PixelSpacing = image_data["PixelRatio"]
    ds.ImagePositionPatient = image_data["SlicePosition"]
    
    try:
        ds.ImageOrientationPatient = image_data["SliceOrientation"]  
    except:
        #SliceOrientation not a key
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    
    ds.AccessionNumber = None
    ds.ReferringPhysicianName = None
    ds.SeriesNumber = None
    ds.StudyID = None
    ds.InstanceNumber = None
    ds.Manufacturer = None
    ds.AcquisitionContextSequence = None
    ds.InstanceNumber = i+1


    # Basic encapsulation of color JPEG
    # https://pydicom.github.io/pydicom/stable/tutorials/pixel_data/compressing.html

    with open(image, 'rb') as f:
        frames = [ f.read() ]
        ds.PixelData = pydicom.encaps.encapsulate(frames)

    with PIL.Image.open(image) as im:
        ds.Rows = im.size[1]
        ds.Columns = im.size[0]
        
        im.thumbnail((thumbnails_width, thumbnails_height))
        thumbnail_buffer = BytesIO()
        im.save(thumbnail_buffer, format="JPEG")

    ds.PlanarConfiguration = 0
    ds.SamplesPerPixel = 3
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PhotometricInterpretation = 'YBR_FULL_422'

    ds['PixelData'].VR = 'OB'  # always for encapsulated pixel data
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    meta = pydicom.dataset.FileMetaDataset()
    meta.TransferSyntaxUID = pydicom.uid.JPEGBaseline8Bit
    ds.file_meta = meta
        
    out : BytesIO = BytesIO()
    ds.save_as(out, write_like_original=False)
    
    response = requests.post('http://localhost:8042/instances', out.getvalue())
    
    response.raise_for_status()
    
    uuid = response.json()["ID"]
    series_uuid = response.json()["ParentSeries"]
    
    r = requests.put(f'http://localhost:8042/instances/{uuid}/attachments/thumbnail', data=thumbnail_buffer.getvalue())
    i += 1
    
for stacked in stacked_images:
    print(stacked)
    image = f"{path_to_project}/{stacked_images[stacked]}"
    camera = os.path.basename(image)
    print(camera)
    ds = pydicom.dataset.Dataset()
    ds.PatientName = 'Periglischrus^calcariflexus'
    ds.PatientID = 'Periglischrus10275665'
    ds.PatientBirthDate = '20200914'
    ds.PatientSex = 'O'

    ds.StudyDate = now.strftime('%Y%m%d')
    ds.StudyTime = now.strftime('%H%M%S')

    ds.ImageType = [ 'DERIVED', 'PRIMARY' ]
    ds.UserContentLabel = stacked
    ds.Laterality = 'L'
    ds.LossyImageCompression = '01'
    ds.Modality = 'XC'  # External-camera photography
    ds.SOPClassUID = pydicom.uid.VLPhotographicImageStorage
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = study_uid

    ds.AccessionNumber = None
    ds.ReferringPhysicianName = None
    ds.SeriesNumber = None
    ds.StudyID = None
    ds.InstanceNumber = None
    ds.Manufacturer = None
    ds.AcquisitionContextSequence = None
    ds.InstanceNumber = i+1


    # Basic encapsulation of color JPEG
    # https://pydicom.github.io/pydicom/stable/tutorials/pixel_data/compressing.html

    with open(image, 'rb') as f:
        frames = [ f.read() ]
        ds.PixelData = pydicom.encaps.encapsulate(frames)

    with PIL.Image.open(image) as im:
        ds.Rows = im.size[1]
        ds.Columns = im.size[0]
        
        im.thumbnail((thumbnails_width, thumbnails_height))
        thumbnail_buffer = BytesIO()
        im.save(thumbnail_buffer, format="JPEG")

    ds.PlanarConfiguration = 0
    ds.SamplesPerPixel = 3
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PhotometricInterpretation = 'YBR_FULL_422'

    ds['PixelData'].VR = 'OB'  # always for encapsulated pixel data
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    meta = pydicom.dataset.FileMetaDataset()
    meta.TransferSyntaxUID = pydicom.uid.JPEGBaseline8Bit
    ds.file_meta = meta
        
    out : BytesIO = BytesIO()
    ds.save_as(out, write_like_original=False)
    
    response = requests.post('http://localhost:8042/instances', out.getvalue())
    
    response.raise_for_status()
    
    uuid = response.json()["ID"]
    series_uuid = response.json()["ParentSeries"]
    
    r = requests.put(f'http://localhost:8042/instances/{uuid}/attachments/thumbnail', data=thumbnail_buffer.getvalue())
    i += 1
    