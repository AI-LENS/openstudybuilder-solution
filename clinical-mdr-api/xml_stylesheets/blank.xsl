<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://openstudybuilder.org">

  <xsl:output method="html"/>
  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="/ODM/Study/@OID"/></title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" />
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" />
        <style>
          body {
          font-family: Arial, sans-serif;
          background-color: #ffffff;
          padding: 0px;
          }

          h1, h2, h3, h4, h5 {
          margin-top: 5px;
          margin-bottom: 5px;
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

          input, textarea {
          background: #eee;
          border: 0.01em solid;
          margin: 0.2em 0;
          height: 1.6em;
          }

          [disabled] {
          opacity: 0.3;
          }

          input[type=radio], input[type=checkbox] {
          box-sizing: border-box;
          background-clip: content-box;
          height: 1em;
          padding: 0.1em;
          width: 1em;
          }

          input[checked] {
          background-color: red;
          }

          input[type=radio] {
          border-radius: 100%;
          }

          .row {
          margin-top: 0px;
          margin-right: 0px;
          margin-left: 0px;
          margin-bottom: 0px;
          width: 100%;
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
          font-weight: 550;
          font-size: 70%;
          border-radius: 0.25rem;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
          width: auto;
          white-space: normal;
          margin: 0.2em;
          }

          .badge-ig {
          display: inline-block;
          padding: 0.25em 0.4em;
          font-size: 90%;
          font-weight: 600;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 0.25rem;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
          }

          .row {
          padding-right: 0px;
          padding-left: 0px;
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
          break-before: page;        /* Modern spec */
          }
          }

        </style>
      </head>
      <body>

        <div class="fixed-top">
          <div class="row d-print-none">
            <div class="col-sm-7 text-left">
              <h3><xsl:value-of select="/ODM/Study/GlobalVariables/StudyName"/></h3>
            </div>
            <div class="col-sm-5 text-right">
              <button type="button" class="btn btn-primary btn-sm floating" data-toggle="collapse" data-target=".help">Implementation guidelines</button>
            </div>
          </div>
        </div>

        <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef"/>

        <div class="row"> <!-- Legend -->
          <div class="col-3 text-right">
            <span class="blackItem">Black labels</span> are Mandatory (otherwise <span class="greenItem">Green</span>)
          </div>
          <div class="col-3 text-center">
            <span class="material-symbols-outlined">lock</span> Lock
          </div>
          <div class="col-sm-3 text-center">
            <em>*</em> Data Entry Required
          </div>
          <div class="col-3 text-left">
            <span class="material-symbols-outlined">account_tree</span> Source Data Verification (SDV)
          </div>
        </div>
        
      </body>
      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
    </html>
  </xsl:template>

  <xsl:template match="ItemDef">
    <xsl:param name="domainNiv" />
    <xsl:param name="itemCondition" />
    
    <xsl:variable name="displayType">
      <xsl:choose>
        <xsl:when test="./Alias/@Context = 'CTDisplay'">checkbox</xsl:when>
        <xsl:when test="./@osb:allowsMultiChoice = 'True'">checkbox</xsl:when>
        <xsl:otherwise>radio</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="labelColor">
      <xsl:choose>
        <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">blackItem</xsl:when>
        <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'No'">greenItem</xsl:when>
        <xsl:otherwise>greenItem</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="mandatory" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory"/>
    
    <div class="row">
      <xsl:if test="$mandatory = 'No'">
        <xsl:attribute name="class">row greenItem</xsl:attribute>
      </xsl:if>
      <xsl:if test="$mandatory = 'Yes'">
        <xsl:attribute name="class">row blackItem</xsl:attribute>
      </xsl:if>

      <xsl:choose>
        <xsl:when test="./@DataType = 'comment'"> <!-- Title -->
          <div class="col-sm-1 {$labelColor} border text-left" /> <!-- Item label column -->
          <div class="col-sm-11 {$labelColor} border text-center">
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
          <div class="col-sm-3 {$labelColor} border text-right"> <!-- Item label column -->
            <i aria-hidden="true" class="v-icon notranslate mr-1 mdi mdi-alpha-i-circle theme--light crfItem--text"></i>
            <xsl:choose>
              <xsl:when test="./Question">
                <xsl:apply-templates select="Question">
                  <xsl:with-param name="lockItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:locked" />
                  <xsl:with-param name="sdvItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:sdv" />
                  <xsl:with-param name="mandatoryItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory" />
                </xsl:apply-templates>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="@Name" />
              </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
              <xsl:when test="./@osb:instruction != 'None'">
                <div class="alert alert-secondary text-left help collapse {$labelColor}" role="alert">
                  <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
                </div>
              </xsl:when>
            </xsl:choose>
          </div>

          <!-- Item field column -->
          <xsl:choose>
            <xsl:when test="MeasurementUnitRef">
              <div class="col-sm-4 {$labelColor} border text-left">
                <input type="{@DataType}" class="{$labelColor}" id="{@OID}" name="{@Name}" min="4" maxlenght="40" size="{@Length}"/>
                <xsl:if test="./Alias/@Context = 'wordFormat'">
                  <xsl:for-each select="./Alias[@Context = 'wordFormat']">
                    &#160;&#160;<xsl:value-of disable-output-escaping="yes" select="@Name" />
                  </xsl:for-each>
                </xsl:if>
              </div>
              <div class="col-sm-1 {$labelColor} border text-right">
                Unit :
              </div>
              <div class="col-sm-3 {$labelColor} border text-left">
                <xsl:for-each select="MeasurementUnitRef">
                  <input type="radio" class="{$labelColor}" id="{@MeasurementUnitOID}" name="{../@OID}" value="{@MeasurementUnitOID}" />
                  &#160;
                  <xsl:apply-templates select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/Symbol" />
                  <br />
                </xsl:for-each>
              </div>
            </xsl:when>
            <xsl:otherwise>
              <div class="col-sm-8 {$labelColor} border text-left">
                <xsl:choose>
                  <xsl:when test="CodeListRef">
                    <xsl:for-each select="CodeListRef">
                      <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                        <input type="{$displayType}" class="{$labelColor}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                        &#160;<xsl:apply-templates select="Decode"/><br />
                      </xsl:for-each>
                      <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                        <input type="{$displayType}" class="{$labelColor}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                        &#160;<xsl:value-of select="@CodedValue" /><br />
                      </xsl:for-each>
                    </xsl:for-each>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:choose>
                      <xsl:when test="@DataType = 'boolean'">
                        <input type="checkbox" id="item{@OID}" name="{@Name}" aria-describedby="basic-addon2"/>
                      </xsl:when>
                      <xsl:when test="./@Origin = 'Protocol Value' or ./@Origin = 'Derived Value'">
                        <xsl:choose>
                          <xsl:when test="./Alias/@Context = 'DEFAULT_VALUE'">
                            <input type="{@DataType}" class="{$labelColor}" id="item{@OID}" name="{@Name}" min="4" maxlenght="{@Length}" size="{@Length}" value="{./Alias[@Context = 'DEFAULT_VALUE']/@Name}" disabled="disabled" />
                          </xsl:when>
                          <xsl:otherwise>
                            <input type="text" class="{$labelColor}" id="item{@OID}" name="{@Name}" min="4" maxlenght="{@Length}" size="{@Length}" aria-describedby="item{@OID}" disabled="disabled" />
                          </xsl:otherwise>
                        </xsl:choose>
                      </xsl:when>
                      <xsl:when test="./Alias/@Context = 'DEFAULT_VALUE'">
                        <input type="{@DataType}" class="{$labelColor}" id="item{@OID}" name="{@Name}" min="4" maxlenght="{@Length}" size="{@Length}" aria-describedby="item{@OID}" value="{./Alias[@Context = 'DEFAULT_VALUE']/@Name}" />
                      </xsl:when>
                      <xsl:otherwise>
                        <input type="{@DataType}" class="{$labelColor}" id="item{@OID}" name="{@Name}" min="4" maxlenght="{@Length}" size="{@Length}"/>
                      </xsl:otherwise>
                    </xsl:choose>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="./Alias/@Context = 'wordFormat'">
                  <xsl:for-each select="./Alias[@Context = 'wordFormat']">
                    &#160;&#160;<xsl:value-of disable-output-escaping="yes" select="@Name" />
                  </xsl:for-each>
                </xsl:if>
              </div>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template match="ItemGroupDef">
    <div class="odmitemgroup">
      <div class="row">
        <div class="col-sm-12 border">
          <h4>
            <span class="badge-itemgroup">G</span>&#160;&#160;<xsl:value-of disable-output-escaping="yes" select="@Name" />

            <xsl:if test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
              <em>&#160;*&#160;</em>
            </xsl:if>
          </h4>
          <xsl:choose>
            <xsl:when test="./@osb:instruction != 'None'">
              <div class="alert alert-secondary text-left help collapse" role="alert">
                <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
              </div>
            </xsl:when>
          </xsl:choose>
        </div>

        <xsl:for-each select="ItemRef">
          <xsl:sort select="@OrderNumber"/>
          <xsl:apply-templates select="//ItemDef[@OID = current()/@ItemOID]">
            <xsl:with-param name="domainNiv" select="../FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@OrderNumber+1"/>
            <xsl:with-param name="itemCondition" select="current()/@CollectionExceptionConditionOID"/>
          </xsl:apply-templates>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>

  <xsl:template match="FormDef" >
    <div class="page-break"></div>
    <div class="content">
      <div class="odmForm">
        <div class="col">
          <h3><span class="badge-form">F</span>&#160;&#160;<i aria-hidden="true" class="v-icon notranslate mr-1 mdi mdi-alpha-f-circle theme--light crfForm--text"></i><xsl:value-of select="@Name" /></h3>
          <xsl:choose>
            <xsl:when test="./@osb:instruction != 'None'">
              <div class="alert alert-secondary text-left help collapse" role="alert">
                <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
              </div>
            </xsl:when>
          </xsl:choose>
        </div>
        <xsl:for-each select="ItemGroupRef">
          <xsl:sort select="current()/@OrderNumber" data-type="number"/>
          <xsl:apply-templates select="//ItemGroupDef[@OID = current()/@ItemGroupOID]"/>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>

  <xsl:template match="Question">
    <xsl:param name="lockItem"/>
    <xsl:param name="sdvItem"/>
    <xsl:param name="mandatoryItem"/>
    <xsl:value-of select="TranslatedText" />&#160;
    <xsl:choose>
      <xsl:when test="($lockItem = 'Yes') and ($sdvItem = 'Yes')">
        <span class="material-symbols-outlined">lock</span>&#160;<span class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:when test="$lockItem = 'Yes'">
        <span class="material-symbols-outlined">lock</span>
      </xsl:when>
      <xsl:when test="$sdvItem = 'Yes'">
        <span class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:otherwise>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="Decode">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template match="Symbol">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template name="Alias">
    <xsl:param name="aliasContext"/>
    <xsl:param name="aliasName"/>
    <br />
    <div class="badge" style="background-color:#3496f0; border: 1px solid #000; color: white;">
      <xsl:value-of disable-output-escaping="yes" select="$aliasContext" />: <xsl:value-of disable-output-escaping="yes" select="$aliasName" />
    </div>
  </xsl:template>

  <xsl:template name="splitter">
    <xsl:param name="remaining-string"/>
    <xsl:param name="pattern"/>
    <xsl:choose>
      <xsl:when test="contains($remaining-string,$pattern)">
        <split-item>
          <span class="badge" style="background-color:#bfffff; border: 1px solid #000;">
            <xsl:value-of select = "normalize-space(substring-before($remaining-string,$pattern))"/>
          </span>
        </split-item>
        <xsl:call-template name="splitter">
          <xsl:with-param name="remaining-string"  select="substring-after($remaining-string,$pattern)"/>
          <xsl:with-param name="pattern"  select="$pattern"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <split-item>
          <span class="badge" style="background-color:#bfffff; border: 1px solid #000;">
            <xsl:value-of select = "normalize-space($remaining-string)"/>
          </span>
        </split-item>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>