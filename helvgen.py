import maya.cmds as cmds
import os
from functools import partial

EXPORT_FOLDER_NAME = "exports"
defaultModelRootPath = "/Users/shanhuang/Desktop/retro_city/zbrush"

class UI(object):
	windowWidth = 512
	modelPanels = []
	models = {}
	_replaceSelection = False

	def show(self):
		cmds.window(title = "Helvgen", width = windowWidth, height = 100)
		self._modelPanelsRoot = cmds.columnLayout()
		self._modelRootPathInput = cmds.textField(tx = defaultModelRootPath, width = windowWidth)
		
		cmds.rowLayout(numberOfColumns = 2)
		cmds.button(label = "Scan for models", command = self.scanModel)
		self._checkBox = cmds.checkBox(label = "Replace selected", onCommand = self._onCheckReplaceSelection, offCommand = self._offCheckReplaceSelection)
		cmds.setParent()

		cmds.setParent()
		cmds.showWindow()

	def scanModel(self, *args):
		self.models.clear()
		modelRootPath = cmds.textField(self._modelRootPathInput, query = True, text = True)
		for root, _, files in os.walk(modelRootPath):
			for file_ in files:
				if file_.lower().endswith("lo.obj"):
					strs = root.split("/")
					if strs[-1] == EXPORT_FOLDER_NAME:
						modelType = strs[-2]
						if modelType not in self.models:
							self.models[modelType] = [ModelMetadata(file_, root)]
						else:
							self.models[modelType].append(ModelMetadata(file_, root))
		self.refresh()

	def applyModel(self, modelMetadata, *args):
		cmds.undoInfo(openChunk = True)
		selected = cmds.ls(selection = True)

		model = Model(cmds.file(modelMetadata.fullPath, i = True, returnNewNodes = True), modelMetadata)
		model.center()
		model.rename()

		oldTranslation = [0, 0, 0]
		oldRotation = [0, 0, 0]
		oldScale = [1, 1, 1]
		if selected:
			oldTranslation = cmds.xform(selected[-1], query = True, translation = True)
			oldRotation = cmds.xform(selected[-1], query = True, rotation = True)
			oldScale = cmds.xform(selected[-1], query = True, scale = True)
			if self._replaceSelection:
				# delay delete to after import because import is not undoable
				cmds.delete(selected[-1])
		model.position(oldTranslation, oldRotation, oldScale)
		cmds.undoInfo(closeChunk = True)

	def clearModelPanels(self):
		for modelPanel in self.modelPanels:
			cmds.deleteUI(modelPanel, layout = True)
		del(self.modelPanels[:])

	def addModelPanels(self):
		for modelType, modelList in self.models.iteritems():
			cmds.setParent(self._modelPanelsRoot)
			modelPanels.append(cmds.frameLayout(label = modelType, borderStyle = 'etchedIn', collapsable = True, collapse = True, width = windowWidth))
			cmds.columnLayout()
			for modelMetadata in modelList:
				cmds.button(label = modelMetadata.filename, command = partial(self.applyModel, modelMetadata))

	def refresh(self):
		self.clearModelPanels()
		self.addModelPanels()

	def _onCheckReplaceSelection(self, _):
		self._replaceSelection = True

	def _offCheckReplaceSelection(self, _):
		self._replaceSelection = False

class Model(object):
	@property
	def transformNode(self):
		return self._transformNode

	def center(self):
		cmds.xform(self._transformNode, centerPivots = True)
		pivot3 = cmds.xform(self._transformNode, query = True, pivots = True)
		cmds.move(-pivot3[0], -pivot3[1], -pivot3[2], self._transformNode)
		cmds.makeIdentity(self._transformNode, apply = True)
		cmds.select(self._transformNode)

	def position(self, translation, rotation, scale):
		cmds.move(translation[0], translation[1], translation[2], self._transformNode)
		cmds.rotate(rotation[0], rotation[1], rotation[2], self._transformNode)
		cmds.scale(scale[0], scale[1], scale[2], self._transformNode)

	def rename(self):
		self._transformNode = cmds.rename(self._transformNode, self._modelMetadata.filename)

	def __init__(self, nodes, modelMetadata):
		self._nodes = nodes
		self._modelMetadata = modelMetadata
		self._transformNode = next((node for node in self._nodes if cmds.nodeType(node) == "transform"), None)


class ModelMetadata(object):

	@property
	def path(self):
		return self._path

	@property
	def filename(self):
		return self._filename

	@property
	def fullPath(self):
		return self._path + "/" + self._filename

	def __init__(self, filename, path):
		self._path = path
		self._filename = filename

ui = UI()
ui.show()