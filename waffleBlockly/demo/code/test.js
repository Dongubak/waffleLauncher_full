// 통신 시작
new QWebChannel(qt.webChannelTransport, function (webChannel) {
    handler = webChannel.objects.handler;
    alert('pypyjsjs');
    // handler.sendData -> 와플런처에 등록된 핸들러

    // button 누르면 실행되는 함수
    handler.getData.connect(function(res){
      var resHead = res.slice(0,4)
      alert(resHead);
      if (resHead === "LOAD") {
        var importedBlocks = handler.loadXML(res)
        var xml = Blockly.Xml.textToDom(importedBlocks);
        Blockly.Xml.domToWorkspace(xml, Code.workspace);
        alert('RUN LOAD');
      };

      if (resHead === "SAVE") {
        var algorithmWithPy = Blockly.Python.workspaceToCode(Code.workspace);
        var xml = Blockly.Xml.workspaceToDom(Code.workspace);
        var xml_text = Blockly.Xml.domToText(xml); 
        handler.sendData('XML' + xml_text)
        handler.sendData('PYPY' + algorithmWithPy)
        alert('RUN SAVE');
      };
    })
});

// 통신 끝