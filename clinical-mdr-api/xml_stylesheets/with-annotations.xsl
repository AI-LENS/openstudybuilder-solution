<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://openstudybuilder.org">

  <xsl:output method="html" />
  <xsl:template match="/">
    <html>
      <head>
        <title>
          <xsl:value-of select="/ODM/Study/@OID" />
        </title>
        <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" />
        <link rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" />
        <link rel="stylesheet"
          href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" />
        <style>
          body {
          font-family: Arial;
          background-color: #ffffff;
          padding: 0px;
          }

          h1, h2, h3, h4, h5 {
          margin-top: 3px;
          margin-bottom: 3px;
          padding: 5px;
          }

          .fixed-top {
          position: fixed;
          top: 0;
          left: 0;
          width: 99%;
          height: 50px;
          padding: 5px;
          background-color: #ffffff;
          color: black;
          line-height: 20px;
          font-size: 12px;
          z-index: 1000;
          }

          .content {
          margin-top: 50px; /* pushes content below the fixed bar */
          padding: 10px;
          }

          .content .odmForm {
          margin-bottom: 0px;
          padding: 10px;
          background-color: #E8EAF0 !important;
          border-radius: 15px; /* Rounded border for the form */
          }

          .odmform {
          background-color: #fff;
          padding: 10px;
          max-width: 99%;
          margin: auto;
          border-radius: 15px; /* Rounded border for the form */
          padding-top: 80px;
          }

          .odmform + .odmform {
          margin-top: 20px; /* space between divs */
          }

          .odmform h2 {
          text-align: center;
          margin-top: 0;
          margin-bottom: 20px;
          }

          .odmitemgroup {
          border-radius: 10px;
          padding: 15px;
          background-color: #6675a340 !important;
          margin-bottom: 20px;
          }

          input[type="text"] {
          padding: 8px;
          border-radius: 6px;
          border: 1px solid #ccc;
          box-sizing: border-box;
          }

          .badge-form {
          display: inline-block;
          padding: 4px 10px;
          font-size: 12px;
          font-weight: bold;
          color: #005ad2;
          background-color: transparent;
          border: 2px solid #005ad2;
          border-radius: 12px;
          }

          .badge-itemgroup {
          display: inline-block;
          padding: 4px 10px;
          font-size: 12px;
          font-weight: bold;
          color: #3b97de;
          background-color: transparent;
          border: 2px solid #3b97de;
          border-radius: 12px;
          }

          .help {
          font-style: italic;
          padding-left: 30px;
          }

          .greenItem {
          color: green !important;
          }

          .blackItem {
          color: black !important;
          }

          .alert {
          position: relative;
          padding: 0.4rem 0.8rem;
          margin-top: 0.2em;
          margin-bottom: 0.2rem;
          border: 1px solid #0000001c;
          border-radius: 0.2rem;
          font-style: italic;
          }

          .alert-secondary {
          background-color: #e2e3e5 !important;
          }

          .alert-danger {
          background-color: #f2dede !important;
          }

          [disabled] {
          opacity: 0.3;
          }

          .row {
          margin-top: 0px;
          margin-right: 0px;
          margin-left: 0px;
          margin-bottom: 0px;
          width: 100%;
          padding-right: 0px;
          padding-left: 0px;
          }

          em {
          font-weight: bold;
          font-style: normal;
          color: #f00;
          }

          .container {
          max-width: 100%;
          }

          .material-symbols-outlined {
          vertical-align: text-bottom;
          }

          .oidinfo {
          color: red !important;
          font-style: normal;
          font-size: 12px;
          }

          .badge {
          display: inline-block;
          margin: 0.2em;
          padding: 0.25em 0.4em;
          font-size: 80%;
          font-weight: 550;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 0px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s
    ease-in-out,box-shadow .15s ease-in-out;
          }

          .badge-ig {
          display: inline-block;
          margin: 0.2em;
          padding: 0.25em 0.4em;
          font-size: 90%;
          font-weight: 600;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 0px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s
    ease-in-out,box-shadow .15s ease-in-out;
          }

          split-item {
          display: block;
          width: 100%;
          }

          split-item .badge .badge-ig {
          }

          @media print {
          .page-break {
          page-break-before: always; /* For older browsers */
          break-before: page; /* Modern spec */
          }
          }

        </style>
      </head>
      <body>

        <div class="fixed-top">
          <div class="row d-print-none">
            <div class="col-sm-6 text-left">
              <h3>
                <xsl:value-of select="/ODM/Study/GlobalVariables/StudyName" />
              </h3>
            </div>
            <div class="col-sm-6 text-right">
              <button type="button" class="btn btn-primary btn-sm" data-toggle="collapse"
                data-target=".help">Implementation guidelines</button>&#160; <button type="button"
                class="btn btn-primary btn-sm" data-toggle="collapse" data-target=".sponsor">Completion
    guidelines</button>&#160; <button type="button" class="btn btn-primary btn-sm"
                data-toggle="collapse" data-target=".cdash">Cdash</button>&#160; <button
                type="button" class="btn btn-primary btn-sm" data-toggle="collapse"
                data-target=".sdtm">SDTM</button>&#160; <button type="button"
                class="btn btn-primary btn-sm" data-toggle="collapse" data-target=".TopicCode">
    TopicCode</button>&#160; <button type="button" class="btn btn-primary btn-sm"
                data-toggle="collapse" data-target=".AdamCode">AdamCode</button>&#160; <button
                type="button" class="btn btn-primary btn-sm" data-toggle="collapse"
                data-target=".oid">Keys</button>
            </div>
          </div>
        </div>

        <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef" />

        <div class="row"> <!-- Legend -->
          <div class="col-3 text-right">
            <span class="blackItem">Black label</span> are Mandatory (otherwise <span
              class="greenItem">Green</span>) </div>
          <div class="col-3 text-center">
            <span class="material-symbols-outlined">lock</span> Lock </div>
          <div class="col-3 text-center">
            <em>*</em> Data Entry Required </div>
          <div class="col-3 text-left">
            <span class="material-symbols-outlined">account_tree</span> Source Data Verification
    (SDV) </div>
        </div>
      </body>
      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"
        integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
        crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
        crossorigin="anonymous"></script>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
    </html>
  </xsl:template>

  <xsl:template match="ItemDef">
    <xsl:param name="domainNiv" />
    <xsl:param name="itemCondition" /> <!-- Not used for the moment -->
    <xsl:param name="domainBckg" />
    
    <xsl:variable
      name="displayType">
      <xsl:choose>
        <xsl:when test="./Alias/@Context = 'CTDisplay'">checkbox</xsl:when>
        <xsl:when test="./@osb:allowsMultiChoice = 'True'">checkbox</xsl:when>
        <xsl:otherwise>radio</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <xsl:variable
      name="labelColor">
      <xsl:choose>
        <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
    blackItem</xsl:when>
        <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'No'">
    greenItem</xsl:when>
        <xsl:otherwise>greenItem</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <xsl:variable
      name="mandatory" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory" />

    <div
      class="row"> <!-- One line -->
      <xsl:if test="$mandatory = 'No'">
        <xsl:attribute name="class">row greenItem</xsl:attribute>
      </xsl:if>
      <xsl:if test="$mandatory = 'Yes'">
        <xsl:attribute name="class">row blackItem</xsl:attribute>
      </xsl:if>

      <xsl:choose>
        <xsl:when test="./@DataType = 'comment'"> <!-- Title -->   
          <div
            class="col-sm-1 {$labelColor} border text-left" /> <!-- Item lable column -->
          <div
            class="col-sm-9 {$labelColor} border text-center"> <!-- Next 11 columns -->
            <xsl:choose>
              <xsl:when test="./Question">
                <xsl:apply-templates select="Question">
                  <xsl:with-param name="lockItem" select="'No'" />
                  <xsl:with-param name="sdvItem" select="'No'" />
                  <xsl:with-param name="mandatoryItem" select="$mandatory" />
                </xsl:apply-templates>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="@Name" />
              </xsl:otherwise>
            </xsl:choose>
          </div>
          <div
            class="col-sm-2 border text-center"> <!-- Annotation -->
            <xsl:choose> <!-- Option with Alias - to display NOT SUBMITTED for example -->
              <xsl:when test="./Alias/@Context = 'Sdtm'">
                <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                  <xsl:call-template name="splitter">
                    <xsl:with-param name="aliasContext" select="'Sdtm'" />
                    <xsl:with-param name="remaining-string" select="./@Name" />
                    <xsl:with-param name="pattern" select="'|'" />
                    <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                  </xsl:call-template>
                </xsl:for-each>
              </xsl:when>
              <xsl:otherwise>
                <xsl:choose>
                  <xsl:when test="@SDSVarName != 'None'">
                    <br />
                    <xsl:call-template name="splitter">
                      <xsl:with-param name="aliasContext" select="'Sdtm'" />
                      <xsl:with-param name="remaining-string" select="@SDSVarName" />
                      <xsl:with-param name="pattern" select="'|'" />
                      <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                    </xsl:call-template>
                  </xsl:when>
                </xsl:choose>
              </xsl:otherwise>
            </xsl:choose>
          </div>
        </xsl:when>
        <xsl:otherwise> <!-- Not a title -->
          <div class="col-sm-1 {$labelColor} border text-left">
            <xsl:if test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
              <em> * </em>
            </xsl:if>
            <xsl:if test="./@osb:locked = 'Yes'">
              <span class="material-symbols-outlined">lock</span>
            </xsl:if>
            <xsl:if test="./@osb:sdv = 'Yes'">
              <span class="material-symbols-outlined">account_tree</span>
            </xsl:if>
          </div>
          <div
            class="col-sm-3 {$labelColor} border text-right"> <!-- Item label column -->
            <i aria-hidden="true"
              class="v-icon notranslate mr-1 mdi mdi-alpha-i-circle theme--light crfItem--text"></i>
            <xsl:choose>
              <xsl:when test="./Question">
                <xsl:apply-templates select="Question">
                  <xsl:with-param name="lockItem"
                    select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:locked" />
                  <xsl:with-param name="sdvItem"
                    select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:sdv" />
                  <xsl:with-param name="mandatoryItem"
                    select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory" />
                </xsl:apply-templates>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="@Name" />
              </xsl:otherwise>
            </xsl:choose>
            <div class="oidinfo oid collapse">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of
                select="@osb:version" />]</div>
            <xsl:for-each select="./Alias[@Context = 'TopicCode']">
              <xsl:call-template name="Alias">
                <xsl:with-param name="aliasContext" select="@Context" />
                <xsl:with-param name="aliasName" select="@Name" />
                <xsl:with-param name="aliasBgcolor" select="'#3496f0'" />
              </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="./Alias[@Context = 'AdamCode']">
              <xsl:call-template name="Alias">
                <xsl:with-param name="aliasContext" select="@Context" />
                <xsl:with-param name="aliasName" select="@Name" />
                <xsl:with-param name="aliasBgcolor" select="'#2f2f2f'" />
              </xsl:call-template>
            </xsl:for-each>
            <xsl:choose>
              <xsl:when test="./@osb:instruction != 'None'">
                <div class="alert alert-secondary text-left help collapse {$labelColor}"
                  role="alert">
                  <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of
                    disable-output-escaping="yes" select="@osb:instruction" />
                </div>
              </xsl:when>
            </xsl:choose>
          </div>

          <!-- Item field column -->
          <xsl:choose>
            <xsl:when test="MeasurementUnitRef">
              <div class="col-sm-3 {$labelColor} border text-left">
                <xsl:choose>
                  <xsl:when test="./@Origin = 'Derived Value'">
                    <input type="{@DataType}" class="{$labelColor} " name="{@Name}" min="4"
                      maxlength="40" size="{@Length}" aria-describedby="basic-addon2"
                      disabled="disabled" /> &#160;<span class="text-center {$labelColor}"
                      id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                  </xsl:when>
                  <xsl:otherwise>
                    <input type="{@DataType}" class="{$labelColor}" name="{@Name}" min="4"
                      maxlength="40" size="{@Length}" aria-describedby="basic-addon2" /> &#160;<span
                      class="text-center {$labelColor}" id="item{@OID}"><xsl:value-of
                        select="@Length" /> digit(s)</span>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                  <xsl:when test="./@osb:sponsorInstruction != 'None'">
                    <div class="alert alert-danger sponsor collapse" role="alert">
                      <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                        disable-output-escaping="yes" select="@osb:sponsorInstruction" />
                    </div>
                  </xsl:when>
                </xsl:choose>
                <xsl:if test="./Alias/@Context = 'wordFormat'">
                  <xsl:for-each select="./Alias[@Context = 'wordFormat']"> &#160;&#160;<xsl:value-of
                      disable-output-escaping="yes" select="@Name" />
                  </xsl:for-each>
                </xsl:if>
              </div>
              <div
                class="col-sm-1 {$labelColor} border text-right">
                Unit:&#160;
              </div>
              <div
                class="col-sm-2 {$labelColor} border text-left">
                <xsl:for-each select="MeasurementUnitRef">
                  <input type="radio" class="{$labelColor}" id="{@MeasurementUnitOID}"
                    name="{../@OID}" value="{@MeasurementUnitOID}" /> &#160; <xsl:apply-templates
                    select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/Symbol" />
    &#160; <span class="oidinfo oid collapse"> [OID=<xsl:value-of select="@MeasurementUnitOID" />,
    Version=<xsl:value-of
                      select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/@osb:version" />
    ]</span>
                  <br />
                </xsl:for-each>
              </div>
              <div
                class="col-sm-2 {$labelColor} border text-center">
                <xsl:call-template name="splitter">
                  <xsl:with-param name="aliasContext" select="'Sdtm'" />
                  <xsl:with-param name="remaining-string" select="@SDSVarName" />
                  <xsl:with-param name="pattern" select="'|'" />
                  <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                </xsl:call-template>
                <xsl:for-each select="./Alias[@Context = 'Cdash']">
                  <xsl:call-template name="splitter">
                    <xsl:with-param name="aliasContext" select="@Context" />
                    <xsl:with-param name="remaining-string" select="./@Name" />
                    <xsl:with-param name="pattern" select="'|'" />
                    <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                  </xsl:call-template>
                </xsl:for-each>
                <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                  <xsl:call-template name="splitter">
                    <xsl:with-param name="aliasContext" select="@Context" />
                    <xsl:with-param name="remaining-string" select="./@Name" />
                    <xsl:with-param name="pattern" select="'|'" />
                    <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                  </xsl:call-template>
                </xsl:for-each>
              </div>
            </xsl:when>
            <xsl:otherwise> <!-- Not a MeasurementUnitRef -->
              <xsl:choose>
                <xsl:when test="CodeListRef"> <!-- A CodeList -->
                  <xsl:for-each select="CodeListRef">
                    <div class="col-sm-6 {$labelColor} border text-left">
                      <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                        <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                        <input
                          type="{$displayType}" class="{$labelColor}" id="{@CodedValue}"
                          name="{../@OID}" value="{@CodedValue}" /> &#160;<xsl:apply-templates
                          select="Decode" />&#160;[<xsl:value-of select="@CodedValue" />]&#160;<br />
                        <span
                          class="oidinfo oid collapse">[OID=<xsl:value-of select="@osb:OID" />,
    Version=<xsl:value-of select="@osb:version" />]</span>
                      </xsl:for-each>
                      <xsl:for-each
                        select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                        <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                        <input
                          type="text" class="{$labelColor} " id="{@CodedValue}" name="{../@OID}"
                          value="{@CodedValue}" /> &#160;<xsl:value-of select="@CodedValue" />&#160;<br />
                        <span
                          class="oidinfo oid collapse">[OID=<xsl:value-of select="@osb:OID" />]</span>
                      </xsl:for-each>
                      <span class="oidinfo oid collapse">[OID=<xsl:value-of select="@CodeListOID" />,
    Version=<xsl:value-of select="//CodeList[@OID = current()/@CodeListOID]/@osb:version" />]</span>
                      <xsl:value-of select="../CodeList[@OID = current()/@CodeListOID]" />
                      <xsl:for-each select="./Alias[@Context = 'TopicCode']">
                        <xsl:call-template name="Alias">
                          <xsl:with-param name="aliasContext" select="@Context" />
                          <xsl:with-param name="aliasName" select="@Name" />
                          <xsl:with-param name="aliasBgcolor" select="'#3496f0'" />
                        </xsl:call-template>
                      </xsl:for-each>
                      <xsl:for-each select="./Alias[@Context = 'AdamCode']">
                        <xsl:call-template name="Alias">
                          <xsl:with-param name="aliasContext" select="@Context" />
                          <xsl:with-param name="aliasName" select="@Name" />
                          <xsl:with-param name="aliasBgcolor" select="'#2f2f2f'" />
                        </xsl:call-template>
                      </xsl:for-each>
                      <xsl:choose>
                        <xsl:when test="../@osb:sponsorInstruction != 'None'">
                          <div class="alert alert-danger sponsor collapse" role="alert">
                            <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                              disable-output-escaping="yes" select="../@osb:sponsorInstruction" />
                          </div>
                        </xsl:when>
                      </xsl:choose>
                    </div>
                    <div
                      class="col-sm-2 {$labelColor} border text-center">
                      <xsl:call-template name="splitter">
                        <xsl:with-param name="aliasContext" select="'Sdtm'" />
                        <xsl:with-param name="remaining-string" select="@SDSVarName" />
                        <xsl:with-param name="pattern" select="'|'" />
                        <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                      </xsl:call-template>
                      <xsl:for-each select="./Alias[@Context = 'Cdash']">
                        <xsl:call-template name="splitter">
                          <xsl:with-param name="aliasContext" select="@Context" />
                          <xsl:with-param name="remaining-string" select="./@Name" />
                          <xsl:with-param name="pattern" select="'|'" />
                          <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                        </xsl:call-template>
                      </xsl:for-each>
                      <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                        <xsl:call-template name="splitter">
                          <xsl:with-param name="aliasContext" select="@Context" />
                          <xsl:with-param name="remaining-string" select="./@Name" />
                          <xsl:with-param name="pattern" select="'|'" />
                          <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                        </xsl:call-template>
                      </xsl:for-each>
                    </div>
                  </xsl:for-each>
                </xsl:when>
                <xsl:otherwise> <!-- Everything else than a CodeList or a MesurementUnit -->
                  <div class="col-sm-6 {$labelColor} border">
                    <xsl:choose>
                      <xsl:when test="@DataType = 'boolean'">
                        <input type="checkbox" id="item{@OID}" name="{@Name}" />
                      </xsl:when>
                      <xsl:when test="./@Origin = 'Protocol Value' or ./@Origin = 'Derived Value'">
                        <xsl:choose>
                          <xsl:when test="./Alias/@Context = 'DEFAULT_VALUE'">
                            <input type="{@DataType}" class="{$labelColor}" id="item{@OID}"
                              name="{@Name}" min="4" maxlength="40" size="{@Length}"
                              aria-describedby="item{@OID}"
                              placeholder="{./Alias[@Context = 'DEFAULT_VALUE']/@Name}"
                              disabled="disabled" /> &#160;<span class="text-center {$labelColor}"
                              id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                          </xsl:when>
                          <xsl:otherwise>
                            <input type="{@DataType}" class="{$labelColor}" id="item{@OID}"
                              name="{@Name}" min="4" maxlength="{@Length}" size="{@Length}"
                              aria-describedby="item{@OID}" disabled="disabled" /> &#160;<span
                              class="text-center {$labelColor}" id="item{@OID}"><xsl:value-of
                                select="@Length" /> digit(s)</span>
                          </xsl:otherwise>
                        </xsl:choose>
                      </xsl:when>
                      <xsl:when test="./Alias/@Context = 'DEFAULT_VALUE'">
                        <input type="{@DataType}" class="{$labelColor}" id="item{@OID}"
                          name="{@Name}" min="4" maxlength="40" size="{@Length}"
                          aria-describedby="item{@OID}"
                          placeholder="{./Alias[@Context = 'DEFAULT_VALUE']/@Name}"
                          aria-label="{@Name}" /> &#160;<span class="text-center {$labelColor}"
                          id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                      </xsl:when>
                      <xsl:otherwise>
                        <input type="{@DataType}" class="{$labelColor}" id="item{@OID}"
                          name="{@Name}" min="4" maxlength="40" size="{@Length}"
                          aria-describedby="item{@OID}" /> &#160;<span
                          class="text-center {$labelColor}" id="item{@OID}"><xsl:value-of
                            select="@Length" /> digit(s)</span>
                      </xsl:otherwise>
                    </xsl:choose>
                    <xsl:if test="./Alias/@Context = 'wordFormat'">
                      <xsl:for-each select="./Alias[@Context = 'wordFormat']"> &#160;&#160;<xsl:value-of
                          disable-output-escaping="yes" select="@Name" />
                      </xsl:for-each>
                    </xsl:if>
                    <xsl:choose>
                      <xsl:when test="./@osb:sponsorInstruction != 'None'">
                        <div class="alert alert-danger sponsor collapse" role="alert">
                          <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                            disable-output-escaping="yes" select="@osb:sponsorInstruction" />
                        </div>
                      </xsl:when>
                    </xsl:choose>
                  </div>
                  <div
                    class="col-sm-2 {$labelColor} border align-items-center text-center">
                    <xsl:call-template name="splitter">
                      <xsl:with-param name="aliasContext" select="'Sdtm'" />
                      <xsl:with-param name="remaining-string" select="@SDSVarName" />
                      <xsl:with-param name="pattern" select="'|'" />
                      <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                    </xsl:call-template>
                    <xsl:for-each select="./Alias[@Context = 'Cdash']">
                      <xsl:call-template name="splitter">
                        <xsl:with-param name="aliasContext" select="@Context" />
                        <xsl:with-param name="remaining-string" select="./@Name" />
                        <xsl:with-param name="pattern" select="'|'" />
                        <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                      </xsl:call-template>
                    </xsl:for-each>
                    <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                      <xsl:call-template name="splitter">
                        <xsl:with-param name="aliasContext" select="@Context" />
                        <xsl:with-param name="remaining-string" select="./@Name" />
                        <xsl:with-param name="pattern" select="'|'" />
                        <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                      </xsl:call-template>
                    </xsl:for-each>
                  </div>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template match="ItemGroupDef">
    <xsl:variable name="domainLevel"
      select="../FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@OrderNumber+1" />
    <xsl:variable
      name="domainBg">
      <xsl:choose>
        <xsl:when test="./@Domain">
          <xsl:for-each select="./osb:DomainColor">
            <xsl:value-of select="." />
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="./Alias/@Context">
          <xsl:for-each select="./Alias/@Context">
            <xsl:choose>
              <xsl:when test="contains(./@Name, 'Note')">
                <xsl:value-of select="substring-after('Note:',@Name)" />
                <xsl:value-of
                  select="':#ffffff !important;'" />
              </xsl:when>
              <xsl:when test="position() = 5">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#0053ad !important;'" />
              </xsl:when>
              <xsl:when test="position() = 4">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#ffbf9c !important;'" />
              </xsl:when>
              <xsl:when test="position() = 3">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#96ff96 !important;'" />
              </xsl:when>
              <xsl:when test="position() = 2">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#ffff96 !important;'" />
              </xsl:when>
              <xsl:when test="position() = 1">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#bfffff !important;'" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#96ff96 !important;'" />
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:when>
      </xsl:choose>
    </xsl:variable>

    <div
      class="odmitemgroup">
      <div class="row">
        <div class="col-sm-10 border">
          <h4>
            <span class="badge-itemgroup">G</span>&#160;&#160;<xsl:value-of select="@Name" />
            <xsl:if
              test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
              <em>&#160;*&#160;</em>
            </xsl:if>
          </h4>
          <div class="oidinfo oid collapse">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of
              select="@osb:version" />]</div>
          <xsl:choose>
            <xsl:when test="./@osb:instruction != 'None'">
              <div class="alert alert-secondary text-left help collapse" role="alert">
                <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of
                  disable-output-escaping="yes" select="@osb:instruction" />
              </div>
            </xsl:when>
          </xsl:choose>
          <xsl:choose>
            <xsl:when test="./@osb:sponsorInstruction != 'None'">
              <div class="alert alert-danger sponsor collapse" role="alert">
                <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                  disable-output-escaping="yes" select="@osb:sponsorInstruction" />
              </div>
            </xsl:when>
          </xsl:choose>
          <xsl:choose>
            <xsl:when test="./Alias/@Context = 'ImplementationNotes'">
              <div class="alert alert-danger d-flex" role="alert">
                <xsl:for-each select="./Alias[@Context = 'ImplementationNotes']">
                  <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                    disable-output-escaping="yes" select="./@Name" />
                </xsl:for-each>
              </div>
            </xsl:when>
          </xsl:choose>
        </div>
        <div class="col-sm-2 border align-items-center text-center">
          <xsl:if test="./@Domain">
            <h4>
              <xsl:call-template name="IGsplitter">
                <xsl:with-param name="remaining-string" select="./@Domain" />
                <xsl:with-param name="pattern" select="'|'" />
                <xsl:with-param name="domainbgcolor" select="$domainBg" />
              </xsl:call-template>
            </h4>
          </xsl:if>
          <xsl:if test="./Alias/@Context = 'Sdtm'">
            <h4>
              <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                <xsl:call-template name="splitter">
                  <xsl:with-param name="aliasContext" select="'Sdtm'" />
                  <xsl:with-param name="remaining-string" select="./@Name" />
                  <xsl:with-param name="pattern" select="'|'" />
                  <xsl:with-param name="domainbgcolor" select="$domainBg" />
                </xsl:call-template>
              </xsl:for-each>
            </h4>
          </xsl:if>
        </div>
      </div>
      <!-- For each Item in an ItemGroup in a Form -->
      <xsl:for-each select="ItemRef">
        <xsl:sort select="@OrderNumber" data-type="number" />
        <xsl:apply-templates
          select="//ItemDef[@OID = current()/@ItemOID]">
          <xsl:with-param name="domainNiv" select="$domainLevel" />
          <xsl:with-param name="domainBckg" select="$domainBg" />
          <xsl:with-param name="itemCondition" select="current()/@CollectionExceptionConditionOID" />
        </xsl:apply-templates>
      </xsl:for-each>
    </div>
  </xsl:template>

  <xsl:template match="FormDef">
    <div class="page-break"></div>
    <div class="content">
      <div class="odmForm">
        <div class="col">
          <h2><span class="badge-form">F</span>&#160;&#160;<xsl:value-of select="@Name" /></h2>
          <span class="oidinfo oid collapse">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of
              select="@osb:version" />]</span>
          <xsl:choose>
            <xsl:when test="./@osb:instruction != 'None'">
              <div class="alert alert-secondary text-left help collapse" role="alert">
                <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of
                  disable-output-escaping="yes" select="@osb:instruction" />
              </div>
            </xsl:when>
          </xsl:choose>
          <xsl:choose>
            <xsl:when test="./@osb:sponsorInstruction != 'None'">
              <div class="alert alert-danger sponsor collapse" role="alert">
                <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of
                  disable-output-escaping="yes" select="@osb:sponsorInstruction" />
              </div>
            </xsl:when>
          </xsl:choose>
        </div>
        <!-- For each ItemGroup in the Form -->
        <xsl:for-each select="ItemGroupRef">
          <xsl:sort select="current()/@OrderNumber" data-type="number" />
          <xsl:apply-templates
            select="//ItemGroupDef[@OID = current()/@ItemGroupOID]" />
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>

  <!-- TEMPLATES -->

  <xsl:template match="Question">
    <xsl:param name="lockItem" />
    <xsl:param name="sdvItem" />
    <xsl:param name="mandatoryItem" />
    <xsl:value-of
      select="TranslatedText" />&#160; <xsl:choose>
      <xsl:when test="($lockItem = 'Yes') and ($sdvItem = 'Yes')">
        <span class="material-symbols-outlined">lock</span>&#160;<span
          class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:when test="$lockItem = 'Yes'">
        <span class="material-symbols-outlined">lock</span>
      </xsl:when>
      <xsl:when test="$sdvItem = 'Yes'">
        <span class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:otherwise> </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="Decode">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template match="Symbol">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template name="Alias">
    <xsl:param name="aliasContext" />
      <xsl:param name="aliasName" />
      <xsl:param name="aliasBgcolor" />
      <div
      class="{$aliasContext} collapse">
      <div class="badge"
        style="background-color:{$aliasBgcolor} !important; border: 1px solid #000; color: white !important;">
        <xsl:value-of disable-output-escaping="yes" select="$aliasName" />
      </div>
    </div>
  </xsl:template>

  <xsl:template name="IGsplitter">
    <xsl:param name="aliasContext" />
    <xsl:param name="remaining-string" />
    <xsl:param name="pattern" />
    <xsl:param
      name="domainbgcolor" />
    <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
          <xsl:value-of select="substring-after($domainbgcolor,substring($remaining-string,1,3))" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#bfffff !important;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <div
      class="{$aliasContext} collapse">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string,$pattern)" />
                </span><br />
              </xsl:when>
              <xsl:otherwise>
                <span class="badge-ig"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important!">
                  <xsl:value-of
                    select="normalize-space(concat(substring-before(substring-before($remaining-string,$pattern),':'),' (', substring-after(substring-before($remaining-string,$pattern),':'),')'))" />
                </span><br />
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
          <xsl:call-template
            name="IGsplitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string"
              select="substring-after($remaining-string,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$itemBg" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span><br />
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span><br />
              </xsl:when>
              <xsl:when test="$remaining-string != ''">
                <span class="badge-ig"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of
                    select="normalize-space(concat(substring-before($remaining-string,':'),' (', substring-after($remaining-string,':'),')'))" />
                </span><br />
              </xsl:when>
              <xsl:otherwise> </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template name="splitter">
    <xsl:param name="aliasContext" />
    <xsl:param name="remaining-string" />
    <xsl:param name="pattern" />
    <xsl:param
      name="domainbgcolor" />
    <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,'Note')">
          <xsl:value-of select="'#ffffff !important;'" />
        </xsl:when>
        <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
          <xsl:value-of
            select="substring(substring-after($domainbgcolor,substring($remaining-string,1,2)),2,8)" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#bfffff !important;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable
      name="remainingstrg">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,':')">
          <xsl:value-of select="substring-after($remaining-string,':')" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$remaining-string" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <div
      class="{$aliasContext} collapse text-left">
      <xsl:choose>
        <xsl:when test="contains($remainingstrg,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
    &#160;
              </xsl:when>
              <xsl:otherwise>
                <span class="badge"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg}! important;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
    &#160;
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
          <xsl:call-template
            name="splitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string"
              select="substring-after($remainingstrg,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$domainbgcolor" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template name="replace-string">
    <xsl:param name="text" />
    <xsl:param name="replace" />
    <xsl:param name="with" />
    <xsl:choose>
      <xsl:when test="contains($text,$replace)">
        <xsl:value-of select="substring-before($text,$replace)" />
        <xsl:value-of select="$with" />
        <xsl:call-template
          name="replace-string">
          <xsl:with-param name="text" select="substring-after($text,$replace)" />
          <xsl:with-param name="replace" select="$replace" />
          <xsl:with-param name="with" select="$with" />
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>