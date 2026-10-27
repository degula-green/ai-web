<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6 font-sans text-slate-800">
    <div class="mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <section class="page-header">
        <div>
          <h1 class="page-title">{{ effectivePageTitle }}</h1>
          <p class="page-subtitle">{{ effectivePageSubtitle }}</p>
        </div>

        <div class="header-actions">
          <button
            class="draft-library-button"
            type="button"
            @click="openDraftLibrary"
          >
            草稿箱<span v-if="currentSceneDraftCount"> {{ currentSceneDraftCount }}</span>
          </button>
          <div class="mode-switch">
            <button class="mode-switch-button" type="button" @click="toggleModeMenu">
              {{ currentModeLabel }}
            </button>
            <div v-if="showModeMenu" class="mode-switch-menu">
              <button
                class="mode-switch-item"
                :class="{ active: currentMode === 'manual' }"
                type="button"
                @click="selectMode('manual')"
              >手动</button>
              <button class="mode-switch-item" type="button" disabled>自动</button>
              <button class="mode-switch-item" type="button" disabled>批量</button>
            </div>
          </div>
          <div class="draft-badge">
            <span v-if="purposeLocked" class="header-purpose-text">{{ videoPurposeScene }}</span>
            <select
              v-else
              v-model="videoPurposeScene"
              class="header-purpose-select"
              title="成片用途：这类数字人视频最终要用来做什么"
            >
              <option value="口播数字人">口播数字人</option>
              <option value="卖货数字人">卖货数字人</option>
              <option value="产品介绍数字人">产品介绍数字人</option>
              <option value="模特数字人">模特数字人</option>
              <option value="视频剪辑数字人">视频剪辑数字人</option>
            </select>
          </div>
        </div>
      </section>

      <div class="grid-layout" :class="gridLayoutClass">
        <div v-if="showFlowColumn" class="flow-column">
          <section v-if="isStepVisible('extract')" class="panel-card panel-accent">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('extract') }}</span>
                <h2>{{ stepTitle('extract') }}</h2>
              </div>
            </div>

            <label class="field-label">视频链接</label>
            <div class="inline-group">
              <input
                v-model.trim="sourceUrl"
                class="field-input flex-1"
                placeholder="请输入抖音 / 小红书 / B站 / 快手等内容链接"
              />
              <button class="primary-button" type="button" :disabled="extractingCopy" @click="handleExtractCopy">
                {{ extractingCopy ? '提取中...' : '提取文案' }}
              </button>
            </div>

            <div class="platform-row">
              <span class="platform-chip" :class="{ active: detectedPlatform === 'dy' }">抖音</span>
              <span class="platform-chip" :class="{ active: detectedPlatform === 'xhs' }">小红书</span>
              <span class="platform-chip" :class="{ active: detectedPlatform === 'bilibili' }">B站</span>
              <span class="platform-chip" :class="{ active: detectedPlatform === 'ks' }">快手</span>
              <span class="platform-chip" :class="{ active: Boolean(detectedPlatform && !knownPlatforms.has(detectedPlatform)) }">
                其他平台
              </span>
            </div>

            <p v-if="extractMeta" class="hint-text">{{ extractMeta }}</p>
            <div v-if="extractResult?.transcript_srt" class="mt-2 flex flex-wrap items-center gap-2">
              <span class="text-xs text-slate-500">原片 ASR 已生成 SRT，可直接烧原视频口播轴</span>
              <button class="ghost-button text-sm" type="button" @click="copyTranscriptSrt">复制 SRT</button>
            </div>

            <label class="field-label">原始文案</label>
            <textarea
              v-model="sourceCopy"
              class="field-area h-[260px]"
              placeholder="解析链接、抓取正文、转录视频后的文案会显示在这里，也支持手动修改"
            />
          </section>

          <section v-if="isStepVisible('rewrite')" class="panel-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('rewrite') }}</span>
                <h2>{{ stepTitle('rewrite') }}</h2>
              </div>
              <span class="panel-tag">正式草稿</span>
            </div>

            <div class="toolbar-grid">
              <select v-model="rewriteTemplate" class="field-input">
                <option value="通用口播模板">通用口播模板</option>
                <option value="知识分享模板">知识分享模板</option>
                <option value="带货转化模板">带货转化模板</option>
              </select>
              <select v-model="rewriteTone" class="field-input">
                <option value="自然口播语气">自然口播语气</option>
                <option value="更强转化语气">更强转化语气</option>
                <option value="更专业一点">更专业一点</option>
              </select>
              <div class="count-chip">{{ sourceCopy.length || 0 }} 字</div>
            </div>

            <div class="inline-group">
              <button class="primary-button flex-1" type="button" :disabled="rewritingCopy" @click="handleRewriteCopy">
                {{ rewritingCopy ? '改写中...' : '一键改写文案' }}
              </button>
              <button class="soft-button flex-1" type="button" :disabled="rewritingCopy" @click="handleOptimizeRewrite">
                AI 迭代调顺
              </button>
            </div>

            <p v-if="rewriteMeta" class="hint-text">{{ rewriteMeta }}</p>

            <label class="field-label">改写结果</label>
            <textarea
              v-model="rewrittenCopy"
              class="field-area h-[240px]"
              placeholder="改写后的文案会显示在这里"
            />
          </section>

          <section v-if="isStepVisible('voice')" class="panel-card feature-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('voice') }}</span>
                <h2>{{ stepTitle('voice') }}</h2>
              </div>
              <button class="text-link" type="button" :disabled="voiceListLoading" @click="loadVoiceOptions">
                {{ voiceListLoading ? '加载中...' : '刷新音色' }}
              </button>
            </div>

            <div class="choice-grid">
              <button class="choice-card" :class="{ active: voiceMode === 'system' }" type="button" @click="voiceMode = 'system'">
                <span class="material-symbols-outlined">library_music</span>
                <strong>系统音色</strong>
                <span>直接选择平台内置音色生成口播</span>
              </button>
              <button class="choice-card" :class="{ active: voiceMode === 'clone' }" type="button" @click="voiceMode = 'clone'">
                <span class="material-symbols-outlined">mic</span>
                <strong>声音复刻</strong>
                <span>上传参考音频，生成你自己的专属音色</span>
              </button>
            </div>

            <div v-if="voiceMode === 'system'" class="mini-grid">
              <div>
                <label class="field-label">选择声音</label>
                <select v-model="selectedVoiceAssetId" class="field-input">
                  <option value="">请选择系统音色</option>
                  <option
                    v-for="voice in systemVoiceOptions"
                    :key="voice.id"
                    :value="String(voice.id)"
                  >
                    {{ voice.voice_name }}
                  </option>
                </select>
              </div>

              <div>
                <label class="field-label">风格</label>
                <select v-model="voiceStyle" class="field-input">
                  <option value="自然陈述">自然陈述</option>
                  <option value="情绪带动">情绪带动</option>
                  <option value="高转化讲解">高转化讲解</option>
                </select>
              </div>
            </div>

            <template v-if="voiceMode === 'clone'">
              <div class="mini-grid">
                <div>
                  <label class="field-label">选择声音</label>
                  <div class="voice-select">
                    <button class="voice-select-trigger" type="button" @click="showCloneVoiceMenu = !showCloneVoiceMenu">
                      <span>{{ selectedCloneVoiceLabel }}</span>
                      <span class="material-symbols-outlined voice-select-arrow">expand_more</span>
                    </button>
                    <div v-if="showCloneVoiceMenu" class="voice-select-menu">
                      <button class="voice-select-option" type="button" @click="selectCloneVoice(null)">
                        <span class="voice-select-name">请选择我的音色</span>
                      </button>
                      <div
                        v-for="voice in userVoiceOptions"
                        :key="voice.id"
                        class="voice-select-row"
                        :class="{ active: String(voice.id) === selectedVoiceAssetId }"
                      >
                        <button class="voice-select-option flex-1" type="button" @click="selectCloneVoice(voice)">
                          <span class="voice-select-name">{{ voice.voice_name }}</span>
                        </button>
                        <button
                          v-if="voice.third_party_voice_id"
                          class="voice-select-delete"
                          type="button"
                          title="删除音色"
                          :disabled="deletingVoice"
                          @click.stop="handleDeleteVoice(voice)"
                        >
                          <span class="material-symbols-outlined">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <label class="field-label">风格</label>
                  <select v-model="voiceStyle" class="field-input">
                    <option value="自然陈述">自然陈述</option>
                    <option value="情绪带动">情绪带动</option>
                    <option value="高转化讲解">高转化讲解</option>
                  </select>
                </div>
              </div>

              <div class="inline-group">
                <button class="soft-button flex-1" type="button" @click="showCloneCreator = !showCloneCreator">
                  {{ showCloneCreator ? '收起添加声音' : '添加声音' }}
                </button>
              </div>

              <p v-if="!userVoiceOptions.length" class="hint-text">当前用户还没有可用的复刻音色，先点击“添加声音”创建。</p>

              <div v-if="showCloneCreator" class="slider-block">
                <div class="mini-grid">
                  <div>
                    <label class="field-label">音色名称</label>
                    <input v-model.trim="cloneVoicePrefix" class="field-input" maxlength="10" placeholder="如 myvoice" />
                  </div>
                  <div>
                    <label class="field-label">参考音频</label>
                    <button class="soft-button w-full" type="button" :disabled="cloneUploading || cloningVoice" @click="openCloneAudioUpload">
                      {{ cloneUploading ? '上传中...' : cloneAudioUrl ? '重新上传音频' : '上传参考音频' }}
                    </button>
                  </div>
                </div>

                <input
                  ref="cloneAudioUploadInput"
                  type="file"
                  class="hidden"
                  accept="audio/*"
                  @change="handleCloneAudioFileChange"
                />

                <div class="slider-row">
                  <span>参考音频要求</span>
                  <strong>10~20 秒</strong>
                </div>
                <p class="hint-text !mt-0">
                  建议读一段连续、自然、无背景噪音的完整口播材料。避免音乐、回声、多人声、长静音。
                  推荐读品牌介绍、产品卖点、个人自我介绍等正常口播文本。
                </p>
                <p class="hint-text !mt-0">
                  最好使用普通话，语速平稳，单人清晰发音，音频时长尽量在 10 到 20 秒之间。
                </p>
                <p v-if="cloneAudioUrl" class="hint-text !mt-0">已上传参考音频，可直接创建复刻音色。</p>

                <button class="primary-button w-full" type="button" :disabled="cloningVoice" @click="handleCloneVoice">
                  {{ cloningVoice ? '创建中...' : '创建复刻音色' }}
                </button>
              </div>
            </template>

            <p v-if="voiceMode === 'system' && selectedVoiceDescription" class="hint-text">{{ selectedVoiceDescription }}</p>

            <div class="slider-block">
              <div class="slider-row">
                <span>语速</span>
                <strong>{{ voiceSpeed.toFixed(1) }}</strong>
              </div>
              <input v-model="voiceSpeedSlider" type="range" class="w-full accent-primary" min="0" max="100" />
            </div>

            <div class="slider-block">
              <div class="slider-row">
                <span>音量</span>
                <strong>{{ voiceSimilarity.toFixed(1) }}</strong>
              </div>
              <input v-model="voiceSimilaritySlider" type="range" class="w-full accent-primary" min="0" max="100" />
            </div>

            <button class="primary-button w-full" type="button" :disabled="generatingVoice" @click="handleGenerateVoice">
              {{ generatingVoice ? '生成中...' : '生成口播音频' }}
            </button>

            <div class="upload-box min-h-[150px]">
              <template v-if="generatedAudioUrl">
                <span class="material-symbols-outlined text-[34px] text-primary/70">graphic_eq</span>
                <strong class="mt-3 text-slate-700">声音试听区</strong>
                <audio :src="generatedAudioUrl" controls class="mt-3 w-full max-w-[320px]" @loadedmetadata="handleGeneratedAudioMetadata"></audio>
                <p class="mt-2 text-xs text-slate-500">音频地址已写入当前草稿，可直接给数字人口播使用</p>
                <p v-if="generatedAudioDurationSeconds > 0" class="mt-1 text-xs text-slate-400">当前音频时长约 {{ formatDuration(generatedAudioDurationSeconds) }}</p>
              </template>
              <template v-else>
                <span class="material-symbols-outlined text-[34px] text-primary/70">graphic_eq</span>
                <strong class="mt-3 text-slate-700">声音试听区</strong>
                <p class="mt-1 text-xs text-slate-500">请先选择系统音色并生成音频</p>
              </template>
            </div>
          </section>
        </div>

        <div v-if="showStudioColumn" class="studio-column">
          <section class="panel-card feature-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('avatar') }}</span>
                <h2>{{ stepTitle('avatar') }}</h2>
              </div>
              <div class="upload-actions">
                <button class="text-link" type="button" :disabled="imageUploading" @click="openImageUpload">
                  {{ imageUploading ? '上传图片中...' : '上传图片' }}
                </button>
              </div>
            </div>

            <div class="mini-grid">
              <div>
                <label class="field-label">数字人模板</label>
                <select v-model="digitalTemplate" class="field-input">
                  <option value="品牌讲解型">品牌讲解型</option>
                  <option value="创始人复刻型">创始人复刻型</option>
                  <option value="直播转化型">直播转化型</option>
                </select>
              </div>

              <div>
                <label class="field-label">出镜场景</label>
                <select v-model="digitalScene" class="field-input">
                  <option value="极简直播间">极简直播间</option>
                  <option value="产品展台">产品展台</option>
                  <option value="办公区背景">办公区背景</option>
                </select>
              </div>
            </div>

            <input
              ref="imageUploadInput"
              type="file"
              class="hidden"
              accept="image/*"
              @change="handleImageFileChange"
            />

            <div class="upload-box min-h-[176px]">
              <template v-if="digitalHumanImageUrl">
                <img :src="digitalHumanImageUrl" alt="数字人形象预览" class="preview-image" @load="handleDigitalHumanImageLoad" />
                <strong class="mt-3 text-slate-700">图片数字人预览</strong>
                <p class="mt-1 text-xs text-slate-500">
                  已上传图片素材，当前草稿会自动保存该地址
                  <template v-if="digitalHumanImageMetaLabel">，{{ digitalHumanImageMetaLabel }}</template>
                </p>
              </template>
              <template v-else>
                <span class="material-symbols-outlined text-[38px] text-primary/70">person_play</span>
                <strong class="mt-3 text-slate-700">数字人形象预览</strong>
                <p class="mt-1 text-xs text-slate-500">请上传单张人物图，后续会与产品图融合后再生成卖货视频</p>
              </template>
            </div>
          </section>

          <section v-if="isStepVisible('model_prompt')" class="panel-card feature-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('model_prompt') }}</span>
                <h2>{{ stepTitle('model_prompt') }}</h2>
              </div>
              <button class="text-link" type="button" :disabled="productsLoading" @click="loadProducts">
                {{ productsLoading ? '加载中...' : '刷新产品' }}
              </button>
            </div>

            <div class="section-stack">
              <div>
                <label class="field-label">产品搜索</label>
                <input
                  v-model.trim="productKeyword"
                  class="field-input"
                  placeholder="搜索品牌产品"
                  @keyup.enter="loadProducts"
                />
              </div>
              <div>
                <label class="field-label">选择产品</label>
                <select v-model="selectedProductId" class="field-input" @change="handleProductChange">
                  <option value="">请选择产品</option>
                  <option v-for="item in productList" :key="item.brandId" :value="item.brandId">
                    {{ item.productName || '未命名产品' }} / {{ item.brandName || '未命名品牌' }}
                  </option>
                </select>
              </div>
            </div>

            <div class="mini-grid">
              <div class="product-asset-field">
                <label class="field-label">产品白底图</label>
                <button
                  class="product-asset-picker-trigger"
                  type="button"
                  @click="openProductAssetPicker('white')"
                >
                  <div class="product-asset-picker-thumb">
                    <img
                      v-if="selectedWhiteAsset"
                      :src="selectedWhiteAsset.thumbnail || selectedWhiteAsset.assetUrl"
                      alt=""
                    />
                    <span v-else class="material-symbols-outlined product-asset-picker-placeholder">image</span>
                  </div>
                  <div class="product-asset-picker-meta">
                    <span class="product-asset-picker-title">选择白底图</span>
                    <span class="product-asset-picker-sub">
                      {{ selectedWhiteImageId ? '已选择，点击更换' : '未选择' }}
                    </span>
                  </div>
                  <span class="material-symbols-outlined product-asset-picker-chevron">chevron_right</span>
                </button>
              </div>
              <div class="product-asset-field">
                <label class="field-label">产品佩戴图</label>
                <button
                  class="product-asset-picker-trigger"
                  type="button"
                  @click="openProductAssetPicker('wear')"
                >
                  <div class="product-asset-picker-thumb">
                    <img
                      v-if="selectedWearAsset"
                      :src="selectedWearAsset.thumbnail || selectedWearAsset.assetUrl"
                      alt=""
                    />
                    <span v-else class="material-symbols-outlined product-asset-picker-placeholder">image</span>
                  </div>
                  <div class="product-asset-picker-meta">
                    <span class="product-asset-picker-title">选择佩戴图</span>
                    <span class="product-asset-picker-sub">
                      {{ selectedWearImageId ? '已选择，点击更换' : '未选择' }}
                    </span>
                  </div>
                  <span class="material-symbols-outlined product-asset-picker-chevron">chevron_right</span>
                </button>
              </div>
            </div>

            <div class="mini-grid">
              <div>
                <div class="panel-subhead">
                  <div>
                    <label class="field-label">指定场景图</label>
                    <p class="field-hint">不上传时默认回退为产品佩戴图</p>
                  </div>
                  <button class="text-link" type="button" :disabled="salesSceneImageUploading" @click="openSalesSceneImageUpload">
                    {{ salesSceneImageUploading ? '上传中...' : salesSceneImageUrl ? '重新上传' : '上传场景图' }}
                  </button>
                </div>
                <input
                  ref="salesSceneImageInput"
                  type="file"
                  class="hidden"
                  accept="image/*"
                  @change="handleSalesSceneImageChange"
                />
                <div class="upload-box min-h-[176px]">
                  <template v-if="salesSceneImageUrl">
                    <img :src="salesSceneImageUrl" alt="场景图预览" class="preview-image" />
                  </template>
                  <template v-else>
                    <span class="material-symbols-outlined empty-icon">landscape</span>
                    <p>上传场景图</p>
                  </template>
                </div>
              </div>
              <div class="section-stack">
                <div class="mini-grid">
                  <div>
                    <label class="field-label">融合张数</label>
                    <select v-model="salesImageCount" class="field-input">
                      <option v-for="count in salesImageCountOptions" :key="count" :value="count">
                        {{ count }} 张
                      </option>
                    </select>
                  </div>
                  <div>
                    <label class="field-label">融合比例</label>
                    <select v-model="salesAspectRatio" class="field-input">
                      <option v-for="ratio in salesAspectRatioOptions" :key="ratio" :value="ratio">
                        {{ ratio }}
                      </option>
                    </select>
                  </div>
                </div>

                <div v-if="!isProductIntroScene">
                  <label class="field-label">补充要求</label>
                  <textarea
                    v-model="salesExtraRequirements"
                    class="field-area h-[120px]"
                    placeholder="例如：单手拿产品，面向镜头，突出货品标签，直播间展示感更强"
                  />
                </div>

                <button class="primary-button" type="button" :disabled="fusionGenerating" @click="generateSalesFusionImages">
                  {{ fusionGenerating ? '融合中...' : '生成产品融合图' }}
                </button>
              </div>
            </div>

            <div v-if="fusionImages.length" class="section-stack">
              <label class="field-label">融合结果</label>
              <div class="fusion-grid">
                <button
                  v-for="(image, index) in fusionImages"
                  :key="`${image.url}-${index}`"
                  class="fusion-card"
                  :class="{ active: isProductIntroScene ? selectedGalleryImageUrls.includes(image.url) : selectedFusionImageUrl === image.url }"
                  type="button"
                  @click="selectFusionImage(image)"
                >
                  <img :src="image.url" alt="" class="fusion-thumb" />
                  <div class="fusion-actions">
                    <span>{{ isProductIntroScene ? `${selectedGalleryImageUrls.includes(image.url) ? '已选' : '待选'} ${index + 1}` : `第 ${index + 1} 张` }}</span>
                    <button class="text-link" type="button" @click.stop="openFusionPreview(image)">放大</button>
                  </div>
                </button>
              </div>
            </div>
          </section>
        </div>

        <div class="preview-column">
          <section class="panel-card preview-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('preview') }}</span>
                <h2>{{ stepTitle('preview') }}</h2>
              </div>
              <button
                v-if="isProductIntroScene"
                class="panel-tag panel-tag-button"
                type="button"
                @click="openInstructionDialog"
              >
                {{ instructionGenerating ? '脚本生成中' : '指令' }}
              </button>
              <span v-else class="panel-tag">成片区</span>
            </div>

            <div class="preview-stage">
              <div class="edit-footer">
                <button
                  class="primary-button flex-1"
                  type="button"
                  :disabled="generatingDigitalHuman || (isProductIntroScene && instructionGenerating)"
                  @click="handleGenerateDigitalHumanVideo"
                >
                  {{ generatingDigitalHuman ? '生成中...' : '生成数字人视频' }}
                </button>
              </div>

              <div class="subtitle-card">
                <div>
                  <p class="field-label !mb-1">生成状态</p>
                  <p class="text-xs text-slate-500">这里会使用第 05 步选中的融合图生成卖货数字人视频</p>
                </div>
                <div class="radio-row">
                  <span>{{ digitalHumanTaskStatusLabel }}</span>
                </div>
              </div>

              <div class="preview-screen">
                <template v-if="generatedVideoUrl">
                  <video :src="generatedVideoUrl" controls class="preview-video"></video>
                  <strong class="mt-3 text-[24px] font-semibold text-slate-800">数字人视频预览</strong>
                  <p class="mt-2 text-sm text-slate-500">数字人视频已生成，后续剪辑完成后可替换为最终成片</p>
                </template>
                <template v-else-if="isProductIntroScene && selectedGalleryImageUrls.length">
                  <div class="grid grid-cols-2 gap-3">
                    <img v-for="url in selectedGalleryImageUrls" :key="url" :src="url" alt="已选产品图" class="preview-image" />
                  </div>
                  <strong class="mt-3 text-[24px] font-semibold text-slate-800">四宫格待生成</strong>
                  <p class="mt-2 text-sm text-slate-500">已选择 {{ selectedGalleryImageUrls.length }} / 4 张图片，生成视频时会自动拼成四宫格</p>
                </template>
                <template v-else-if="selectedFusionImageUrl">
                  <img :src="selectedFusionImageUrl" alt="融合图预览" class="preview-image" />
                  <strong class="mt-3 text-[24px] font-semibold text-slate-800">待驱动融合图</strong>
                  <p class="mt-2 text-sm text-slate-500">{{ isProductIntroScene ? '先继续选择到 4 张，生成时会自动拼成四宫格视频输入图' : '已选中产品融合图，点击上方按钮即可生成卖货数字人视频' }}</p>
                </template>
                <template v-else>
                  <span class="material-symbols-outlined text-[46px] text-primary/70">play_circle</span>
                  <strong class="mt-3 text-[24px] font-semibold text-slate-800">预览区域</strong>
                  <p class="mt-2 text-sm text-slate-500">{{ isProductIntroScene ? '请先生成产品图，并选择 4 张组成四宫格' : '请先完成产品融合，并选一张融合图作为最终驱动图' }}</p>
                </template>
              </div>

            </div>
          </section>

          <section class="panel-card edit-panel">
            <div class="panel-head">
              <div>
                <span class="panel-step">{{ stepNumber('clip') }}</span>
                <h2>{{ stepTitle('clip') }}</h2>
              </div>
              <span class="panel-tag">主控区</span>
            </div>

            <label class="field-label">视频标题</label>
            <input
              v-model.trim="clipVideoTitle"
              class="field-input clip-video-title-input"
              maxlength="60"
              placeholder="提取文案后可自动填入，也可手动修改"
            />

            <div class="subtitle-card">
              <div class="subtitle-setting-shell">
                <div class="subtitle-setting-title">字幕设置（关闭字幕后，才可以使用模板）</div>
                <div class="subtitle-setting-row">
                  <span class="subtitle-setting-dot"></span>
                  <span class="subtitle-setting-label">启用</span>
                  <button
                    class="toggle-switch clip-toggle-switch"
                    :class="{ active: subtitleSettingsEnabled }"
                    type="button"
                    @click="subtitleSettingsEnabled = !subtitleSettingsEnabled"
                  >
                    <span class="toggle-switch__thumb"></span>
                  </button>

                  <button
                    class="subtitle-setting-btn"
                    type="button"
                    :disabled="!subtitleSettingsEnabled"
                    @click="openSubtitleSettings"
                  >
                    <span class="subtitle-setting-btn__icon">A</span>
                    <span>字幕设置</span>
                  </button>

                  <button
                    class="subtitle-template-tag"
                    :class="{ disabled: subtitleSettingsEnabled }"
                    type="button"
                    :disabled="subtitleSettingsEnabled"
                    @click="openClipTemplateLibrary"
                  >
                    <span class="subtitle-template-tag__icon">田</span>
                    <span class="subtitle-template-tag__name">{{ selectedTitleTemplatePresetLabel }}</span>
                    <span class="subtitle-template-tag__code">{{ selectedTitleTemplatePresetCode }}</span>
                  </button>

                  <span class="subtitle-template-link">{{ subtitleSettingsEnabled ? '字幕：设置' : '字幕：模板' }}</span>
                </div>
              </div>
            </div>
            <div v-if="clipTemplateRuntimeFormVisible" class="subtitle-card clip-template-runtime-card">
              <div class="subtitle-setting-shell clip-template-runtime-shell">
                <div class="clip-template-runtime-head">
                  <div>
                    <strong>模板文案</strong>
                    <p>{{ selectedTitleTemplateDescription }}</p>
                  </div>
                  <span class="clip-template-runtime-title">主标题跟随视频标题</span>
                </div>
                <div class="mini-grid">
                  <label v-if="selectedTitleTemplateSupportsSubtitle" class="field-block">
                    <span class="field-label">副标题</span>
                    <input
                      v-model.trim="overlaySubtitle"
                      class="field-input"
                      maxlength="28"
                      placeholder="输入第二行标题，可选"
                    />
                  </label>
                  <label v-if="selectedTitleTemplateSupportsTag" class="field-block">
                    <span class="field-label">角标文案</span>
                    <input
                      v-model.trim="overlayTag"
                      class="field-input"
                      maxlength="12"
                      placeholder="如 简化版 / 干货 / 必看"
                    />
                  </label>
                </div>
              </div>
            </div>

            <input
              ref="backgroundUploadInput"
              type="file"
              class="hidden"
              :accept="backgroundMode === 'video_fill' ? 'video/*' : 'image/*'"
              @change="handleBackgroundFileChange"
            />
            <input
              ref="bgmUploadInput"
              type="file"
              class="hidden"
              accept="audio/*"
              @change="handleBgmFileChange"
            />

            <div class="mini-grid volume-grid-clip">
              <div class="slider-block clip-slider-card">
                <div class="slider-row">
                  <span>人声音量</span>
                  <strong>{{ voiceVolume.toFixed(1) }}</strong>
                </div>
                <input v-model="voiceVolumeSlider" type="range" class="w-full accent-primary" min="0" max="100" />
              </div>

              <div class="slider-block clip-slider-card">
                <div class="slider-row">
                  <span>BGM 音量</span>
                  <strong>{{ bgmVolume.toFixed(1) }}</strong>
                </div>
                <input v-model="bgmVolumeSlider" type="range" class="w-full accent-primary" min="0" max="100" />
              </div>
            </div>

            <div class="edit-footer">
              <button
                class="primary-button flex-1 clip-submit-button"
                type="button"
                :disabled="clippingVideo"
                @click="runClipRender"
              >
                {{ clippingVideo ? '剪辑中…' : '剪辑视频' }}
              </button>
            </div>
            <p v-if="clipRenderStage || clipRenderDisabledReason" class="hint-text" :class="{ 'text-red-500': !clipRenderStage && clipRenderDisabledReason }">
              {{ clipRenderStage || clipRenderDisabledReason }}
            </p>
            <div class="mt-4 rounded-lg border border-slate-200 bg-white p-3">
              <div class="clip-preview-style-head">
                <p class="text-xs text-slate-500">剪辑样式预览</p>
                <button
                  type="button"
                  class="clip-preview-expand-trigger"
                  @click="clipStylePreviewExpanded = !clipStylePreviewExpanded"
                >
                  <span>{{ clipStylePreviewExpanded ? '收起' : '展开预览' }}</span>
                  <span class="material-symbols-outlined" aria-hidden="true">{{ clipStylePreviewExpanded ? 'expand_less' : 'south' }}</span>
                </button>
              </div>
              <div
                v-show="clipStylePreviewExpanded"
                class="template-live-preview-stage template-live-preview-stage--compact mt-2"
                :style="{ aspectRatio: `${previewCanvasSize.width} / ${previewCanvasSize.height}` }"
              >
                <img v-if="previewBaseImageUrl" :src="previewBaseImageUrl" alt="剪辑样式预览" class="template-preview-media" />
                <div v-else class="template-preview-empty">
                  <span class="material-symbols-outlined">play_circle</span>
                  <p>{{ previewStageEmptyMessage }}</p>
                </div>
                <svg
                  v-if="previewBaseImageUrl"
                  class="template-render-overlay"
                  :viewBox="`0 0 ${previewCanvasSize.width} ${previewCanvasSize.height}`"
                  preserveAspectRatio="none"
                >
                  <g v-if="renderPreviewTitle">
                    <text
                      :x="renderPreviewTitle.x"
                      :y="renderPreviewTitle.y"
                      :font-size="renderPreviewTitle.fontSize"
                      :fill="renderPreviewTitle.color"
                      :text-anchor="renderPreviewTitle.anchor"
                      dominant-baseline="hanging"
                      class="template-render-text template-render-title"
                    >{{ renderPreviewTitle.text }}</text>
                    <text
                      v-if="renderPreviewTitle.subtitle"
                      :x="renderPreviewTitle.x"
                      :y="renderPreviewTitle.y + renderPreviewTitle.fontSize + 14"
                      :font-size="renderPreviewTitle.subtitleSize"
                      :fill="renderPreviewTitle.subtitleColor"
                      :text-anchor="renderPreviewTitle.anchor"
                      dominant-baseline="hanging"
                      class="template-render-text template-render-title-subtitle"
                    >{{ renderPreviewTitle.subtitle }}</text>
                  </g>
                  <g v-if="renderPreviewSubtitle">
                    <rect
                      v-if="renderPreviewSubtitle.showBox"
                      :x="renderPreviewSubtitle.boxX"
                      :y="renderPreviewSubtitle.boxY"
                      :width="renderPreviewSubtitle.boxWidth"
                      :height="renderPreviewSubtitle.boxHeight"
                      :fill="renderPreviewSubtitle.boxColor"
                      :stroke="renderPreviewSubtitle.borderColor"
                      :stroke-width="renderPreviewSubtitle.borderWidth"
                    />
                    <text
                      :x="renderPreviewSubtitle.x"
                      :y="renderPreviewSubtitle.y"
                      :font-size="renderPreviewSubtitle.fontSize"
                      :fill="renderPreviewSubtitle.color"
                      :text-anchor="renderPreviewSubtitle.anchor"
                      dominant-baseline="hanging"
                      class="template-render-text template-render-subtitle"
                    >{{ renderPreviewSubtitle.text }}</text>
                  </g>
                </svg>
              </div>
            </div>
            <div v-if="clippedPreviewUrl" class="mt-4 rounded-lg border border-slate-200 bg-white p-3">
              <p class="text-xs text-slate-500">字幕成片预览（基于改写文案与转录时间轴）</p>
              <video :src="clippedPreviewUrl" controls class="preview-video mt-2 max-h-[320px] w-full rounded-md" />
            </div>
          </section>
        </div>
      </div>
    </div>

    <div
      v-if="productAssetPickerKind"
      class="draft-library-mask"
      role="dialog"
      aria-modal="true"
      @click.self="closeProductAssetPicker"
    >
      <div class="draft-library-dialog product-asset-picker-dialog">
        <div class="draft-library-head">
          <div>
            <h3>{{ productAssetPickerKind === 'white' ? '选择产品白底图' : '选择产品佩戴图' }}</h3>
            <p>点击下方缩略图即可选中并关闭弹窗。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-close" type="button" @click="closeProductAssetPicker">取消</button>
          </div>
        </div>
        <div class="product-asset-picker-grid">
          <button
            v-for="asset in productImageAssets"
            :key="`${productAssetPickerKind}-${asset.id}`"
            type="button"
            class="product-asset-picker-option"
            :class="{
              active:
                productAssetPickerKind === 'white'
                  ? selectedWhiteImageId === asset.id
                  : selectedWearImageId === asset.id,
            }"
            @click="confirmProductAssetPick(asset.id)"
          >
            <img :src="asset.thumbnail || asset.assetUrl" alt="" />
            <span v-if="asset.tags?.length" class="product-asset-picker-tag">{{ asset.tags[0] }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDraftLibrary" class="draft-library-mask" @click.self="closeDraftLibrary">
      <div class="draft-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>草稿箱</h3>
            <p>默认打开新草稿，你可以从这里回到之前的版本。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" @click="handleCreateNewContent">新建内容</button>
            <button class="draft-library-close" type="button" @click="closeDraftLibrary">关闭</button>
          </div>
        </div>

        <div v-if="draftLibraryLoading" class="draft-library-empty">草稿加载中...</div>
        <div v-else-if="!draftLibraryItems.length" class="draft-library-empty">当前没有可恢复的草稿</div>
        <div v-else class="draft-library-list">
          <div
            v-for="item in draftSummaries"
            :key="item.id"
            class="draft-library-item"
          >
            <button
              class="draft-library-main"
              type="button"
              @click="handleSelectDraft(item.id, item.scene)"
            >
              <strong>{{ item.title }}</strong>
              <span>{{ item.scene }}</span>
              <span>{{ formatDraftTime(item.updatedAt) }}</span>
              <span>{{ item.status }}</span>
            </button>
            <button
              class="draft-library-publish"
              type="button"
              @click="handlePublishDraft(item.id)"
            >
              上传
            </button>
            <button
              class="draft-library-delete"
              type="button"
              @click="handleDeleteDraft(item.id)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showSubtitleSettings" class="draft-library-mask" @click.self="closeSubtitleSettings">
      <div class="draft-library-dialog subtitle-settings-dialog">
        <div class="draft-library-head">
          <div>
            <h3>字幕设置</h3>
            <p>只调字幕风格、字号、位置和对齐方式。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-close" type="button" @click="closeSubtitleSettings">关闭</button>
          </div>
        </div>

        <div class="subtitle-settings-body">
          <div class="template-live-preview-stage template-live-preview-stage--compact" :style="{ aspectRatio: `${previewCanvasSize.width} / ${previewCanvasSize.height}` }">
            <img v-if="previewBaseImageUrl" :src="previewBaseImageUrl" alt="字幕设置预览" class="template-preview-media" />
            <div v-else class="template-preview-empty">
              <span class="material-symbols-outlined">play_circle</span>
              <p>{{ previewStageEmptyMessage }}</p>
            </div>
            <svg
              v-if="previewBaseImageUrl"
              class="template-render-overlay"
              :viewBox="`0 0 ${previewCanvasSize.width} ${previewCanvasSize.height}`"
              preserveAspectRatio="none"
            >
              <g v-if="renderPreviewTitle">
                <text
                  :x="renderPreviewTitle.x"
                  :y="renderPreviewTitle.y"
                  :font-size="renderPreviewTitle.fontSize"
                  :fill="renderPreviewTitle.color"
                  :text-anchor="renderPreviewTitle.anchor"
                  dominant-baseline="hanging"
                  class="template-render-text template-render-title"
                >{{ renderPreviewTitle.text }}</text>
                <text
                  v-if="renderPreviewTitle.subtitle"
                  :x="renderPreviewTitle.x"
                  :y="renderPreviewTitle.y + renderPreviewTitle.fontSize + 14"
                  :font-size="renderPreviewTitle.subtitleSize"
                  :fill="renderPreviewTitle.subtitleColor"
                  :text-anchor="renderPreviewTitle.anchor"
                  dominant-baseline="hanging"
                  class="template-render-text template-render-title-subtitle"
                >{{ renderPreviewTitle.subtitle }}</text>
              </g>
              <g v-if="renderPreviewSubtitle">
                <rect
                  v-if="renderPreviewSubtitle.showBox"
                  :x="renderPreviewSubtitle.boxX"
                  :y="renderPreviewSubtitle.boxY"
                  :width="renderPreviewSubtitle.boxWidth"
                  :height="renderPreviewSubtitle.boxHeight"
                  :fill="renderPreviewSubtitle.boxColor"
                  :stroke="renderPreviewSubtitle.borderColor"
                  :stroke-width="renderPreviewSubtitle.borderWidth"
                />
                <text
                  :x="renderPreviewSubtitle.x"
                  :y="renderPreviewSubtitle.y"
                  :font-size="renderPreviewSubtitle.fontSize"
                  :fill="renderPreviewSubtitle.color"
                  :text-anchor="renderPreviewSubtitle.anchor"
                  dominant-baseline="hanging"
                  class="template-render-text template-render-subtitle"
                >{{ renderPreviewSubtitle.text }}</text>
              </g>
            </svg>
          </div>

          <div class="radio-row">
            <label v-for="item in subtitleModeOptions" :key="item.value">
              <input v-model="subtitleMode" :value="item.value" type="radio" name="subtitle-modal" class="accent-primary" />
              {{ item.label }}
            </label>
          </div>

          <div class="mini-grid">
            <div class="slider-block">
              <div class="slider-row">
                <span>字幕字号</span>
                <strong>{{ subtitleFontSize }} px</strong>
              </div>
              <input v-model="subtitleFontSizeSlider" type="range" class="w-full accent-primary" min="28" max="64" step="2" />
            </div>

            <div class="slider-block">
              <div class="slider-row">
                <span>字幕底部偏移</span>
                <strong>{{ subtitleOffsetY }} px</strong>
              </div>
              <input v-model="subtitleOffsetYSlider" type="range" class="w-full accent-primary" min="24" max="180" step="4" />
            </div>
          </div>

          <div>
            <p class="field-label !mb-2">字幕对齐</p>
            <div class="segmented-control">
              <button
                v-for="item in subtitleAlignOptions"
                :key="item.value"
                class="segmented-control__item"
                :class="{ active: subtitleAlign === item.value }"
                type="button"
                @click="subtitleAlign = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showClipTemplateLibrary" class="draft-library-mask" @click.self="closeClipTemplateLibrary">
      <div class="draft-library-dialog clip-template-dialog clip-template-dialog-v2">
        <div class="draft-library-head">
          <input
            v-if="clipTemplateCreatorOpen"
            v-model.trim="clipTemplateDraft.name"
            class="clip-template-editor-title"
            type="text"
            placeholder="新建模板"
          />
          <div v-else>
            <h3>选择视频模板</h3>
          </div>
          <div class="draft-library-actions">
            <template v-if="clipTemplateCreatorOpen">
              <button class="draft-library-secondary" type="button" @click="clipTemplateCreatorOpen = false">返回</button>
              <button class="draft-library-secondary" type="button" :disabled="savingClipTemplate" @click="saveClipTemplateDraft">
                {{ savingClipTemplate ? '保存中…' : '保存模板' }}
              </button>
            </template>
            <template v-else>
              <button class="draft-library-secondary" type="button" :disabled="clipTemplatesLoading" @click="openClipTemplateCreator">新增</button>
              <button class="draft-library-close" type="button" @click="closeClipTemplateLibrary">关闭</button>
            </template>
          </div>
        </div>

        <div v-if="!clipTemplateCreatorOpen" class="clip-template-library clip-template-library-v2">
          <p v-if="clipTemplatesLoading" class="hint-text">模板加载中…</p>
          <div
            v-for="item in visibleClipTemplateCards"
            :key="item.value"
            class="clip-template-card clip-template-card-v2"
            :class="{ active: selectedClipTemplate === item.value }"
            role="button"
            tabindex="0"
            @click="applyClipTemplate(item.value)"
            @keydown.enter.prevent="applyClipTemplate(item.value)"
          >
            <button
              v-if="isUserClipTemplateCard(item)"
              class="clip-template-card__settings"
              type="button"
              title="编辑模板"
              @click.stop="editClipTemplate(item.value)"
            >
              <span class="material-symbols-outlined">settings</span>
            </button>
            <div class="clip-template-card__preview" :class="`template-preview-${item.value}`">
              <img
                v-if="clipTemplateCardThumbnail(item)"
                :src="clipTemplateCardThumbnail(item)"
                :alt="item.label"
                class="clip-template-card__cover-image"
              />
              <template v-else>
                <div v-if="item.titleTemplate !== 'none'" class="clip-template-card__demo-title">主标题</div>
                <div class="clip-template-card__demo-subtitle">字幕预览</div>
              </template>
            </div>
            <div class="clip-template-card__body">
              <strong>{{ item.label }}</strong>
            </div>
          </div>
        </div>

        <div v-else class="clip-template-editor-grid">
          <section class="clip-template-cover-panel">
            <h4>模板封面</h4>
            <button
              class="clip-template-cover-box"
              :class="{ 'has-cover': clipTemplateDraft.coverAdded || clipTemplateDraft.coverUrl }"
              type="button"
              :disabled="clipTemplateCoverUploading"
              @click="openClipTemplateCoverUpload"
            >
              <img
                v-if="clipTemplateDraft.coverUrl"
                :src="clipTemplateDraft.coverUrl"
                alt="模板封面"
                class="clip-template-cover-image"
              />
              <div v-if="clipTemplateDraft.coverUrl" class="clip-template-cover-preview">
                <div
                  v-if="clipTemplateDraft.titleMode !== 'none'"
                  class="clip-template-cover-title"
                  :class="clipTemplateDraft.titleAlign"
                  :style="clipTemplateTitlePreviewStyle"
                >
                  <strong>{{ clipTemplatePreviewTitleText }}</strong>
                  <span>{{ clipTemplatePreviewSubtitleText }}</span>
                </div>
                <div
                  v-if="clipTemplateDraft.titleMode === 'badge'"
                  class="clip-template-cover-badge"
                  :style="clipTemplateBadgePreviewStyle"
                >
                  {{ clipTemplatePreviewBadgeText }}
                </div>
                <div
                  class="clip-template-cover-subtitle"
                  :class="[clipTemplateDraft.subtitleAlign, `sub-${clipTemplateDraft.subtitleMode}`]"
                  :style="clipTemplateSubtitlePreviewStyle"
                >
                  <span>{{ previewCaptionText }}</span>
                  <span v-if="clipTemplateDraft.subtitleDoubleLine">第二行字幕预览</span>
                </div>
              </div>
              <span v-else class="clip-template-cover-plus">+</span>
              <span class="clip-template-cover-tip">
                {{ clipTemplateCoverUploading ? '上传中...' : clipTemplateDraft.coverUrl ? '更换封面' : '上传封面' }}
              </span>
            </button>
            <input
              ref="clipTemplateCoverUploadInput"
              type="file"
              class="hidden"
              accept="image/*"
              @change="handleClipTemplateCoverFileChange"
            />
          </section>

          <section class="clip-template-editor-fields">
            <div class="clip-template-section">
              <div class="clip-template-section-head">
                <strong>标题设置</strong>
                <span>标题</span>
              </div>
              <div class="clip-template-segmented">
                <button
                  v-for="item in clipTemplateTitleModes"
                  :key="item.value"
                  class="clip-template-segment"
                  :class="{ active: clipTemplateDraft.titleMode === item.value }"
                  type="button"
                  @click="clipTemplateDraft.titleMode = item.value"
                >
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.description }}</span>
                </button>
              </div>
              <div v-if="clipTemplateDraft.titleMode !== 'none'" class="mini-grid mt-3">
                <label class="field-block">
                  <span class="field-label">副标题内容</span>
                  <input v-model="clipTemplateDraft.titleSubtitleText" class="field-input" placeholder="输入模板默认副标题" />
                </label>
                <label v-if="clipTemplateDraft.titleMode === 'badge'" class="field-block">
                  <span class="field-label">角标内容</span>
                  <input v-model="clipTemplateDraft.badgeText" class="field-input" placeholder="输入角标文案" />
                </label>
              </div>
              <div class="mini-grid mt-3">
                <label class="field-block">
                  <span class="field-label">标题对齐</span>
                  <select v-model="clipTemplateDraft.titleAlign" class="field-input">
                    <option value="top-left">顶部左对齐</option>
                    <option value="top-center">顶部居中</option>
                    <option value="bottom-left">底部左对齐</option>
                  </select>
                </label>
                <label class="field-block">
                  <span class="field-label">标题字体样式</span>
                  <select v-model="clipTemplateDraft.titleFont" class="field-input">
                    <option value="default">标准</option>
                    <option value="bold">加粗</option>
                    <option value="brand">品牌感</option>
                    <option value="serif">衬线感</option>
                  </select>
                </label>
              </div>
              <div class="clip-template-slider-grid">
                <label class="clip-template-slider">
                  <span>标题大小 <b>{{ clipTemplateDraft.titleSize }}</b></span>
                  <input v-model.number="clipTemplateDraft.titleSize" type="range" min="18" max="40" step="1" />
                </label>
                <label class="clip-template-slider">
                  <span>标题 X 偏移 <b>{{ clipTemplateDraft.titleOffsetX }}</b></span>
                  <input v-model.number="clipTemplateDraft.titleOffsetX" type="range" min="-120" max="120" step="2" />
                </label>
                <label class="clip-template-slider">
                  <span>标题 Y 偏移 <b>{{ clipTemplateDraft.titleOffsetY }}</b></span>
                  <input v-model.number="clipTemplateDraft.titleOffsetY" type="range" min="-160" max="160" step="2" />
                </label>
                <label class="clip-template-slider">
                  <span>副标题大小 <b>{{ clipTemplateDraft.titleSubtitleSize }}</b></span>
                  <input v-model.number="clipTemplateDraft.titleSubtitleSize" type="range" min="10" max="24" step="1" />
                </label>
                <label class="clip-template-slider">
                  <span>角标大小 <b>{{ clipTemplateDraft.badgeSize }}</b></span>
                  <input v-model.number="clipTemplateDraft.badgeSize" type="range" min="10" max="22" step="1" />
                </label>
                <label class="clip-template-slider">
                  <span>角标 X 偏移 <b>{{ clipTemplateDraft.badgeOffsetX }}</b></span>
                  <input v-model.number="clipTemplateDraft.badgeOffsetX" type="range" min="-120" max="120" step="2" />
                </label>
                <label class="clip-template-slider">
                  <span>角标 Y 偏移 <b>{{ clipTemplateDraft.badgeOffsetY }}</b></span>
                  <input v-model.number="clipTemplateDraft.badgeOffsetY" type="range" min="-120" max="120" step="2" />
                </label>
                <label class="field-block">
                  <span class="field-label">角标字体样式</span>
                  <select v-model="clipTemplateDraft.badgeFont" class="field-input">
                    <option value="default">标准</option>
                    <option value="bold">加粗</option>
                    <option value="brand">品牌感</option>
                  </select>
                </label>
              </div>
            </div>

            <div class="clip-template-section">
              <div class="clip-template-section-head">
                <strong>背景设置</strong>
                <span>背景</span>
              </div>
              <div class="clip-template-asset-row">
                <span>{{ backgroundAssetLabel }}</span>
                <div>
                  <button class="soft-button" type="button" @click="openBackgroundLibrary">选择背景素材</button>
                  <button class="ghost-button" type="button" @click="openTemplateBackgroundUpload">上传文件</button>
                </div>
              </div>
            </div>

            <div class="clip-template-section">
              <div class="clip-template-section-head">
                <strong>背景音乐</strong>
                <span>音乐</span>
              </div>
              <div class="clip-template-asset-row">
                <span>{{ bgmAssetUrl ? '已选择背景音乐' : '未选择背景音乐' }}</span>
                <div>
                  <button class="soft-button" type="button" @click="showTemplateBgmLibrary = true">选择背景音乐</button>
                  <button class="ghost-button" type="button" @click="openBgmUpload">上传文件</button>
                </div>
              </div>
              <div class="clip-template-slider-grid clip-template-slider-grid--single">
                <label class="clip-template-slider">
                  <span>背景音乐音量 <b>{{ clipTemplateDraft.bgmVolume }}</b></span>
                  <input v-model.number="clipTemplateDraft.bgmVolume" type="range" min="0" max="100" step="5" />
                </label>
              </div>
            </div>

            <div class="clip-template-section">
              <div class="clip-template-section-head">
                <strong>字幕设置</strong>
                <span>字幕</span>
              </div>
              <div class="clip-template-segmented">
                <button
                  v-for="item in clipTemplateSubtitleModes"
                  :key="item.value"
                  class="clip-template-segment"
                  :class="{ active: clipTemplateDraft.subtitleMode === item.value }"
                  type="button"
                  @click="clipTemplateDraft.subtitleMode = item.value"
                >
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.description }}</span>
                </button>
              </div>
              <div class="mini-grid mt-3">
                <label class="field-block">
                  <span class="field-label">字幕对齐</span>
                  <select v-model="clipTemplateDraft.subtitleAlign" class="field-input">
                    <option value="center">居中</option>
                    <option value="left">左对齐</option>
                  </select>
                </label>
                <label class="field-block">
                  <span class="field-label">字幕字体样式</span>
                  <select v-model="clipTemplateDraft.subtitleFont" class="field-input">
                    <option value="default">标准</option>
                    <option value="bold">加粗</option>
                    <option value="brand">品牌感</option>
                    <option value="serif">衬线感</option>
                  </select>
                </label>
              </div>
              <div class="clip-template-slider-grid">
                <label class="clip-template-slider">
                  <span>字幕大小 <b>{{ clipTemplateDraft.subtitleSize }}</b></span>
                  <input v-model.number="clipTemplateDraft.subtitleSize" type="range" min="12" max="28" step="1" />
                </label>
                <label class="clip-template-slider">
                  <span>字幕 X 偏移 <b>{{ clipTemplateDraft.subtitleOffsetX }}</b></span>
                  <input v-model.number="clipTemplateDraft.subtitleOffsetX" type="range" min="-120" max="120" step="2" />
                </label>
                <label class="clip-template-slider">
                  <span>字幕 Y 偏移 <b>{{ clipTemplateDraft.subtitleOffsetY }}</b></span>
                  <input v-model.number="clipTemplateDraft.subtitleOffsetY" type="range" min="-180" max="120" step="2" />
                </label>
                <div class="clip-template-toggle-card">
                  <span>双行字幕</span>
                  <button
                    class="toggle-switch clip-toggle-switch"
                    :class="{ active: clipTemplateDraft.subtitleDoubleLine }"
                    type="button"
                    @click="clipTemplateDraft.subtitleDoubleLine = !clipTemplateDraft.subtitleDoubleLine"
                  >
                    <span class="toggle-switch__thumb"></span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <div v-if="showTemplateBgmLibrary" class="draft-library-mask" @click.self="showTemplateBgmLibrary = false">
      <div class="draft-library-dialog background-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>选择背景音乐</h3>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button">刷新素材</button>
            <button class="draft-library-close" type="button" @click="showTemplateBgmLibrary = false">关闭</button>
          </div>
        </div>
        <div class="background-upload-bar">
          <div class="status-card">
            <span class="status-dot"></span>
            <span>当前筛选：背景音乐</span>
          </div>
          <button class="soft-button" type="button" @click="openBgmUpload">上传新背景音乐</button>
        </div>
        <div class="background-library-sections">
          <section class="background-library-section">
            <div class="background-section-head">
              <h4>官方背景音乐</h4>
              <span>0 个</span>
            </div>
            <div class="draft-library-empty">当前还没有官方背景音乐素材。</div>
          </section>
          <section class="background-library-section">
            <div class="background-section-head">
              <h4>我的背景音乐</h4>
              <span>{{ bgmAssetUrl ? 1 : 0 }} 个</span>
            </div>
            <div v-if="bgmAssetUrl" class="background-asset-grid">
              <button class="background-asset-card active" type="button" @click="showTemplateBgmLibrary = false">
                <div class="background-asset-thumb template-bgm-thumb"></div>
                <strong>已上传背景音乐</strong>
                <span>我的背景音乐</span>
              </button>
            </div>
            <div v-else class="draft-library-empty">你还没有上传背景音乐。</div>
          </section>
        </div>
      </div>
    </div>

    <div v-if="showInstructionDialog" class="draft-library-mask" @click.self="closeInstructionDialog">
      <div class="draft-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>工作流指令</h3>
            <p>这里展示 AI 根据融合图自动生成的产品介绍文案，生成时会写入工作流的 text 文本。</p>
          </div>
          <div class="draft-library-actions">
            <button
              class="draft-library-secondary"
              type="button"
              :disabled="instructionGenerating || !fusionImages.length"
              @click="handleRegenerateProductInstruction"
            >
              {{ instructionGenerating ? '生成中...' : '重新生成' }}
            </button>
            <button class="draft-library-close" type="button" @click="closeInstructionDialog">关闭</button>
          </div>
        </div>

        <div class="background-library-body">
          <label class="field-label">指令文本</label>
          <p v-if="instructionGenerating" class="hint-text">AI 正在根据最新融合图生成 15 秒分镜口播脚本。</p>
          <p v-else-if="instructionGenerationError" class="hint-text text-rose-500">{{ instructionGenerationError }}</p>
          <textarea
            :value="salesExtraRequirements"
            class="field-area h-[320px]"
            readonly
            :placeholder="instructionGenerating ? 'AI 正在生成脚本...' : '生成产品融合图后，系统会自动写入这里的工作流文案'"
          />
        </div>
      </div>
    </div>

    <div v-if="fusionPreviewImage" class="draft-library-mask" @click.self="closeFusionPreview">
      <div class="draft-library-dialog image-preview-dialog">
        <div class="draft-library-head">
          <div>
            <h3>融合图预览</h3>
            <p>确认选中的卖货数字人融合效果。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" @click="selectFusionImage(fusionPreviewImage)">
              设为驱动图
            </button>
            <button class="draft-library-close" type="button" @click="closeFusionPreview">关闭</button>
          </div>
        </div>
        <div class="image-preview-body">
          <img :src="fusionPreviewImage.url" class="image-preview-full" />
        </div>
      </div>
    </div>

    <div v-if="showBackgroundLibrary" class="draft-library-mask" @click.self="closeBackgroundLibrary">
      <div class="draft-library-dialog background-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>选择背景素材</h3>
            <p>支持保留原背景、使用你上传的背景，或直接选择平台提供的官方背景。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" :disabled="backgroundAssetsLoading" @click="loadBackgroundAssets">
              {{ backgroundAssetsLoading ? '刷新中...' : '刷新素材' }}
            </button>
            <button class="draft-library-close" type="button" @click="closeBackgroundLibrary">关闭</button>
          </div>
        </div>

        <div class="background-library-body">
          <div class="background-choice-grid">
            <button class="choice-card" type="button" :class="{ active: backgroundMode === 'original' }" @click="selectBuiltInBackground('original')">
              <span class="material-symbols-outlined">movie</span>
              <strong>原视频背景</strong>
              <span>保留当前数字人成片原始背景</span>
            </button>
            <button class="choice-card" type="button" :class="{ active: backgroundMode === 'image_fill' }" @click="switchBackgroundMediaType('image_fill')">
              <span class="material-symbols-outlined">image</span>
              <strong>图片背景</strong>
              <span>适合直播间、海报墙、品牌视觉图</span>
            </button>
            <button class="choice-card" type="button" :class="{ active: backgroundMode === 'video_fill' }" @click="switchBackgroundMediaType('video_fill')">
              <span class="material-symbols-outlined">videocam</span>
              <strong>视频背景</strong>
              <span>适合动态场景、办公区或产品氛围视频</span>
            </button>
          </div>

          <div class="background-upload-bar">
            <div class="status-card">
              <span class="status-dot"></span>
              <span>{{ backgroundMode === 'video_fill' ? '当前筛选：视频背景素材' : backgroundMode === 'image_fill' ? '当前筛选：图片背景素材' : '当前选择：原视频背景' }}</span>
            </div>
            <button
              v-if="backgroundMode === 'image_fill' || backgroundMode === 'video_fill'"
              class="soft-button"
              type="button"
              :disabled="backgroundUploading"
              @click="openBackgroundUpload"
            >
              {{ backgroundUploading ? '上传中...' : backgroundMode === 'video_fill' ? '上传新背景视频' : '上传新背景图片' }}
            </button>
          </div>

          <div v-if="backgroundMode === 'image_fill' || backgroundMode === 'video_fill'" class="background-library-sections">
            <section class="background-library-section">
              <div class="background-section-head">
                <h4>官方背景</h4>
                <span>{{ officialBackgroundAssets.length }} 个</span>
              </div>
              <div v-if="officialBackgroundAssets.length" class="background-asset-grid">
                <button
                  v-for="asset in officialBackgroundAssets"
                  :key="asset.id"
                  class="background-asset-card"
                  :class="{ active: backgroundAssetId === asset.id }"
                  type="button"
                  @click="applyBackgroundAsset(asset)"
                >
                  <div class="background-asset-thumb">
                    <img v-if="asset.media_type === 'image'" :src="asset.thumbnail_url || asset.asset_url" :alt="asset.name" />
                    <video v-else :src="asset.thumbnail_url || asset.asset_url" muted playsinline preload="metadata"></video>
                  </div>
                  <strong>{{ asset.name }}</strong>
                  <span>{{ asset.media_type === 'video' ? '官方视频背景' : '官方图片背景' }}</span>
                </button>
              </div>
              <div v-else class="draft-library-empty">当前还没有官方背景素材，可先由平台在表中预置几条记录。</div>
            </section>

            <section class="background-library-section">
              <div class="background-section-head">
                <h4>我的背景</h4>
                <span>{{ userBackgroundAssets.length }} 个</span>
              </div>
              <div v-if="userBackgroundAssets.length" class="background-asset-grid">
                <div
                  v-for="asset in userBackgroundAssets"
                  :key="asset.id"
                  class="background-asset-card"
                  :class="{ active: backgroundAssetId === asset.id }"
                >
                  <button
                    class="background-asset-select"
                    type="button"
                    @click="applyBackgroundAsset(asset)"
                  >
                    <div class="background-asset-thumb">
                      <img v-if="asset.media_type === 'image'" :src="asset.thumbnail_url || asset.asset_url" :alt="asset.name" />
                      <video v-else :src="asset.thumbnail_url || asset.asset_url" muted playsinline preload="metadata"></video>
                    </div>
                    <strong>{{ asset.name }}</strong>
                    <span>{{ asset.media_type === 'video' ? '我上传的视频背景' : '我上传的图片背景' }}</span>
                  </button>
                  <button class="background-asset-delete" type="button" @click.stop="deleteBackgroundAsset(asset)">
                    删除
                  </button>
                </div>
              </div>
              <div v-else class="draft-library-empty">你还没有上传背景素材，可直接在这里上传。</div>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { buildDraftlessQuery } from '../lib/avatarSceneNavigation'
import { getAvatarSceneFlowConfig, type AvatarPurposeScene, type AvatarStepKey } from './creation-avatar-scenes'

import { ApiError, getApiBaseUrl, request } from '../api/http'
import { getBrandProfile, getVisualAssets, listBrandProducts } from '../api/brandInjection'
import { authStore } from '../auth/store'
import { taskStore, type AsyncTask } from '../data-collection/taskStore'
import type { BrandProductCard, BrandProfile, VisualAssetItem } from '../types/brandInjection'

interface ExtractCopyResponse {
  url: string
  parsed_link: {
    platform: string
    content_id: string
    original_url: string
    is_short_link: boolean
  }
  content_info: {
    title?: string
    desc?: string
    author_name?: string
    content_type?: string
  }
  transcript?: {
    text?: string
    segments?: Array<Record<string, unknown>>
  } | null
  /** 由 transcript.segments 生成的标准 SRT（提取时 include_transcript_srt） */
  transcript_srt?: string | null
  extracted_copy: string
  llm_config_name?: string | null
  model_name?: string | null
}

interface RewriteCopyResponse {
  source_text: string
  rewritten_text: string
  instruction?: string | null
  llm_config_name?: string | null
  model_name?: string | null
}

type SubtitleTimelineSegment = {
  start: number
  end: number
  text: string
}

interface CreationDraftRead {
  draft_id: string
  user_id: number
  title?: string | null
  source_url?: string | null
  platform?: string | null
  content_id?: string | null
  content_info: Record<string, unknown>
  transcript: Record<string, unknown>
  extracted_copy?: string | null
  rewrite_instruction?: string | null
  rewritten_copy?: string | null
  voice_params: Record<string, unknown>
  digital_human_params: Record<string, unknown>
  clip_params: Record<string, unknown>
  status: string
  created_at: string
  updated_at: string
}

interface CreationDraftListResponse {
  items: CreationDraftRead[]
}

interface AvatarSalesDraftRead {
  draft_id: string
  user_id: number
  title?: string | null
  source_url?: string | null
  platform?: string | null
  content_id?: string | null
  content_info: Record<string, unknown>
  transcript: Record<string, unknown>
  extracted_copy?: string | null
  rewrite_instruction?: string | null
  rewritten_copy?: string | null
  voice_params: Record<string, unknown>
  digital_human_params: Record<string, unknown>
  clip_params: Record<string, unknown>
  product_keyword?: string | null
  selected_product_id?: string | null
  selected_product_profile: Record<string, unknown>
  product_assets: Array<Record<string, unknown>>
  selected_white_image_id?: string | null
  selected_wear_image_id?: string | null
  scene_image_url?: string | null
  image_count: number
  aspect_ratio: string
  extra_requirements?: string | null
  fusion_task_id?: string | null
  fusion_task_status?: string | null
  fusion_images: Array<Record<string, unknown>>
  selected_fusion_image_url?: string | null
  status: string
  created_at: string
  updated_at: string
}

interface AvatarSalesDraftListResponse {
  items: AvatarSalesDraftRead[]
}

interface ProductInstructionGenerateResponse {
  draft: AvatarSalesDraftRead
  generated_instruction: string
  used_image_urls: string[]
  llm_config_name?: string | null
  model_name?: string | null
}

interface AvatarDraftIndexRead {
  draft_id: string
  user_id: number
  scene_code: 'talk' | 'sales' | 'product' | 'model' | string
  title?: string | null
  status: string
  current_step_code?: string | null
  progress?: number | null
  created_at: string
  updated_at: string
}

interface AvatarDraftIndexListResponse {
  items: AvatarDraftIndexRead[]
}

interface LegacyDraftListItem {
  draft_id: string
  title?: string | null
  status: string
  updated_at: string
  transcript?: Record<string, unknown>
  extracted_copy?: string | null
  rewritten_copy?: string | null
  voice_params?: Record<string, unknown>
  digital_human_params?: Record<string, unknown>
  clip_params?: Record<string, unknown>
}

interface DigitalHumanAssetUpdatePayload {
  media_type: 'image' | 'video'
  file_url: string
  human_type?: 'image' | 'video'
}

interface ClipRenderResponse {
  draft: CreationDraftRead
  srt_preview: string
  playback_requires_auth: boolean
}

interface UploadTicketRead {
  module: string
  media_type: string
  object_name: string
  upload_method: string
  upload_url: string
  file_url: string
  content_type: string
  expires_in_seconds: number
}

interface BackgroundAssetRead {
  id: number
  user_id?: number | null
  name: string
  media_type: 'image' | 'video'
  asset_url: string
  thumbnail_url?: string | null
  source_type: 'official' | 'user' | string
  status: string
  sort_order: number
  created_at: string
  updated_at: string
}

interface BackgroundAssetListResponse {
  items: BackgroundAssetRead[]
}

interface VideoEditTemplateRead {
  id: number
  user_id?: number | null
  name: string
  description: string
  template_type: string
  scene_code: string
  render_config: ClipRenderConfig
  editor_config: Record<string, unknown>
  thumbnail_url?: string | null
  source_type: 'official' | 'user' | string
  status: string
  sort_order: number
  created_at: string
  updated_at: string
}

interface VideoEditTemplateListResponse {
  items: VideoEditTemplateRead[]
}

interface ClipRenderConfig {
  version: number
  canvas: {
    width: number
    height: number
    fps: number
    aspectMode: 'source' | 'fixed'
    sourceWidth?: number
    sourceHeight?: number
  }
  background: {
    mode: string
    assetUrl: string | null
    assetName?: string | null
    fit: 'cover' | 'contain'
  }
  title: {
    enabled: boolean
    mode: string
    text: string
    subtitle: string
    badge: string
    align: 'left' | 'center' | 'right'
    x: number
    y: number
    fontSize: number
    subtitleFontSize: number
    badgeFontSize: number
    fontWeight: number
    color: string
    subtitleColor: string
    badgeColor: string
    borderColor: string
    box: boolean
    boxColor: string
    badgeX: number
    badgeY: number
  }
  subtitle: {
    enabled: boolean
    mode: string
    align: 'left' | 'center' | 'right'
    x: number
    y: number
    fontSize: number
    fontWeight: number
    color: string
    background: string
    borderColor: string
    borderWidth: number
    doubleLine: boolean
  }
  audio: {
    voiceVolume: number
    bgmUrl: string | null
    bgmVolume: number
  }
}

interface TtsVoiceOption {
  id: number
  voice_name: string
  voice_code: string
  source_type?: string | null
  model_name?: string | null
  target_model?: string | null
  third_party_voice_id?: string | null
  voice_gender?: string | null
  voice_language?: string | null
  voice_style?: string | null
  voice_desc?: string | null
  preview_audio_url?: string | null
  status?: string | null
}

interface TtsVoiceListResponse {
  code: number
  message: string
  data?: {
    list?: TtsVoiceOption[]
    total?: number
  }
}

interface TtsGenerateResponse {
  code: number
  message: string
  data?: {
    record_id?: number
    audio_url?: string
    local_audio_url?: string
    request_id?: string
    voice_id?: string
    voice_asset_id?: number
  }
}

interface TtsCloneResponse {
  code: number
  message: string
  data?: {
    id?: number
    voice_id?: string
    status?: string
    request_id?: string
  }
}

interface TtsVoiceDetailResponse {
  code: number
  message: string
  data?: {
    voice_id?: string
    voice_asset?: TtsVoiceOption & {
      owner_user_id?: number | null
    }
  }
}

const titleTemplateOptions = [
  { value: 'none', label: '不加标题', description: '只保留当前字幕，不额外叠加顶部标题', supportsSubtitle: false, supportsTag: false },
  { value: 'headline_white', label: '白字大标题', description: '顶部单行白字大标题，适合常规知识口播', supportsSubtitle: false, supportsTag: false },
  { value: 'headline_white_orange', label: '白橙双标题', description: '第一行白字，第二行橙字，更像短视频爆款封面感', supportsSubtitle: true, supportsTag: false },
  { value: 'headline_box', label: '底色标题条', description: '标题带半透明底色块，适合背景较花的视频', supportsSubtitle: true, supportsTag: false },
  { value: 'headline_tag', label: '双标题+角标', description: '顶部双标题，右上角带小角标，适合教程/干货类', supportsSubtitle: true, supportsTag: true },
  { value: 'headline_gold', label: '金色标题', description: '金色粗体标题，适合励志、语录、观点输出', supportsSubtitle: true, supportsTag: false },
] as const

const clipTemplateOptions = [
  {
    value: 'manual_subtitle',
    code: 'T0',
    label: '不用模板',
    description: '保留当前字幕设置，模板区不接管标题和排版。',
    titleTemplate: 'none',
    subtitleMode: 'default',
    subtitleFontSize: 42,
    subtitleOffsetY: 64,
    subtitleAlign: 'center',
  },
  {
    value: 'talk_clean',
    code: 'T1',
    label: '黄白字幕',
    description: '字幕更醒目，适合知识分享和轻节奏口播。',
    titleTemplate: 'headline_white',
    subtitleMode: 'default',
    subtitleFontSize: 44,
    subtitleOffsetY: 60,
    subtitleAlign: 'center',
  },
  {
    value: 'talk_brand',
    code: 'T2',
    label: '品牌讲解',
    description: '标题更突出，适合品牌介绍、卖点说明。',
    titleTemplate: 'headline_white_orange',
    subtitleMode: 'brand',
    subtitleFontSize: 42,
    subtitleOffsetY: 62,
    subtitleAlign: 'left',
  },
  {
    value: 'talk_digital',
    code: 'T3',
    label: '数字闪字幕',
    description: '字幕和标题更强调冲击感，适合短促信息输出。',
    titleTemplate: 'headline_box',
    subtitleMode: 'digital',
    subtitleFontSize: 46,
    subtitleOffsetY: 58,
    subtitleAlign: 'center',
  },
  {
    value: 'talk_tag',
    code: 'T5',
    label: '高频讲解',
    description: '上方标题和角标并用，适合教程、干货、分步骤内容。',
    titleTemplate: 'headline_tag',
    subtitleMode: 'default',
    subtitleFontSize: 42,
    subtitleOffsetY: 66,
    subtitleAlign: 'center',
  },
  {
    value: 'talk_gold',
    code: 'T6',
    label: '百搭模板',
    description: '自动压暗画面上边缘，标题更稳，适合大多数口播。',
    titleTemplate: 'headline_gold',
    subtitleMode: 'brand',
    subtitleFontSize: 44,
    subtitleOffsetY: 64,
    subtitleAlign: 'center',
  },
] as const

const subtitleModeOptions = [
  { value: 'default', label: '默认字幕' },
  { value: 'brand', label: '品牌字幕' },
  { value: 'digital', label: '数字风字幕' },
] as const

const subtitleAlignOptions = [
  { value: 'left', label: '左对齐' },
  { value: 'center', label: '居中' },
  { value: 'right', label: '右对齐' },
] as const

interface DigitalHumanSubmitResponse {
  detect?: Record<string, unknown> | null
  job?: {
    output?: {
      task_id?: string
      task_status?: string
      submit_time?: string
      task_type?: string
    }
    request_id?: string
  }
}

interface DigitalHumanTaskResponse {
  output?: {
    task_id?: string
    task_status?: string
    submit_time?: string
    scheduled_time?: string
    end_time?: string
    results?: Array<{
      orig_prompt?: string
      actual_prompt?: string
      url?: string
      video_url?: string
    }> | {
      orig_prompt?: string
      actual_prompt?: string
      url?: string
      video_url?: string
    }
    video_url?: string
  }
  request_id?: string
}

interface CreationAvatarViewProps {
  purposeScene?: AvatarPurposeScene
  purposeLocked?: boolean
  pageTitle?: string
  pageSubtitle?: string
}

interface DraftSummary {
  id: string
  title: string
  status: string
  updatedAt: string
  scene: AvatarPurposeScene
}

interface GalleryImageItem {
  url: string
  output_type?: string
  source_url?: string
  persisted?: boolean
}

interface SalesScenePersistedState {
  product_keyword?: string | null
  selected_product_id?: string | null
  selected_product_profile?: BrandProfile | null
  product_assets?: VisualAssetItem[]
  selected_white_image_id?: string | null
  selected_wear_image_id?: string | null
  scene_image_url?: string | null
  image_count?: number | null
  aspect_ratio?: string | null
  extra_requirements?: string | null
  fusion_task_id?: string | null
  fusion_task_status?: string | null
  fusion_images?: GalleryImageItem[]
  selected_fusion_image_url?: string | null
  selected_gallery_image_urls?: string[] | null
  collage_image_url?: string | null
}

const props = withDefaults(defineProps<CreationAvatarViewProps>(), {
  purposeScene: '口播数字人',
  purposeLocked: false,
  pageTitle: '内容创作台',
  pageSubtitle: '提取爆款文案、改写文案，并将声音参数、数字人参数统一沉淀到创作草稿',
})

const route = useRoute()
const router = useRouter()

const purposeSceneRouteMap: Record<AvatarPurposeScene, string> = {
  '口播数字人': '/content-creation/digital-human/talk',
  '卖货数字人': '/content-creation/digital-human/sales',
  '产品介绍数字人': '/content-creation/digital-human/product',
  '模特数字人': '/content-creation/digital-human/model',
  '视频剪辑数字人': '/content-creation/digital-human/clip',
}

const purposeSceneCodeMap: Record<AvatarPurposeScene, string> = {
  '口播数字人': 'talk',
  '卖货数字人': 'sales',
  '产品介绍数字人': 'product',
  '模特数字人': 'model',
  '视频剪辑数字人': 'clip',
}

const sceneCodePurposeMap: Record<string, AvatarPurposeScene> = {
  talk: '口播数字人',
  sales: '卖货数字人',
  product: '产品介绍数字人',
  model: '模特数字人',
  clip: '视频剪辑数字人',
}

const knownPlatforms = new Set(['dy', 'xhs', 'bilibili', 'ks'])
const copywritingApiBaseUrl = (
  import.meta.env.VITE_REMIX_AGENT_API_BASE_URL
  ?? import.meta.env.VITE_AGENT_API_BASE_URL
  ?? 'http://localhost:8002'
).replace(/\/$/, '')
const salesImageCountOptions = [4, 6, 8]
const salesAspectRatioOptions = ['1:1', '3:4', '9:16']

const sourceUrl = ref('')
const sourceCopy = ref('')
const rewrittenCopy = ref('')
const extractingCopy = ref(false)
const rewritingCopy = ref(false)
const rewriteTemplate = ref('通用口播模板')
const rewriteTone = ref('自然口播语气')
const extractResult = ref<ExtractCopyResponse | null>(null)
const rewriteResult = ref<RewriteCopyResponse | null>(null)

const draftId = ref('')
const draftSaving = ref(false)
const draftLoading = ref(false)
const hydratingDraft = ref(false)
const draftLibraryLoading = ref(false)
const showDraftLibrary = ref(false)
const showInstructionDialog = ref(false)
const instructionGenerating = ref(false)
const instructionGenerationError = ref('')
const draftLibraryItems = ref<AvatarDraftIndexRead[]>([])
const currentMode = ref<'manual' | 'auto' | 'batch'>('manual')
const showModeMenu = ref(false)
const switchingScene = ref(false)
let draftSaveTimer: ReturnType<typeof setTimeout> | null = null
const imageUploadInput = ref<HTMLInputElement | null>(null)
const videoUploadInput = ref<HTMLInputElement | null>(null)
const cloneAudioUploadInput = ref<HTMLInputElement | null>(null)
const backgroundUploadInput = ref<HTMLInputElement | null>(null)
const bgmUploadInput = ref<HTMLInputElement | null>(null)
const imageUploading = ref(false)
const videoUploading = ref(false)
const cloneUploading = ref(false)
const backgroundUploading = ref(false)
const bgmUploading = ref(false)
const cloningVoice = ref(false)
const deletingVoice = ref(false)
const showCloneVoiceMenu = ref(false)
const digitalHumanImageUrl = ref('')
const digitalHumanVideoUrl = ref('')
const digitalHumanImageWidth = ref(0)
const digitalHumanImageHeight = ref(0)
const digitalHumanVideoWidth = ref(0)
const digitalHumanVideoHeight = ref(0)
const generatedAudioDurationSeconds = ref(0)
const voiceTimelineSegments = ref<SubtitleTimelineSegment[]>([])

const voiceMode = ref<'system' | 'clone'>('system')
const showCloneCreator = ref(false)
const voiceProfile = ref('新闻男声')
const voiceStyle = ref('自然陈述')
const voiceSpeedSlider = ref('50')
const voiceSimilaritySlider = ref('30')
const voiceListLoading = ref(false)
const generatingVoice = ref(false)
const voiceOptions = ref<TtsVoiceOption[]>([])
const selectedVoiceAssetId = ref('')
const selectedVoiceId = ref('')
const cloneAudioUrl = ref('')
const cloneVoicePrefix = ref('myvoice')
const generatedAudioUrl = ref('')
const generatedAudioLocalUrl = ref('')
const generatedAudioSourceUrl = ref('')
const previewFrameDataUrl = ref('')
const previewFrameWidth = ref(0)
const previewFrameHeight = ref(0)
const previewFrameLoading = ref(false)
let previewFrameRequestId = 0
const generatedVoiceRecordId = ref<number | null>(null)
const generatingDigitalHuman = ref(false)
const digitalHumanTaskId = ref('')
const digitalHumanTaskStatus = ref('')
const generatedVideoUrl = ref('')
const generatedVideoSourceUrl = ref('')
let digitalHumanTaskTimer: ReturnType<typeof setTimeout> | null = null
const finalizedDigitalHumanTaskNo = ref('')
const humanType = ref<'image' | 'video'>('image')
const digitalTemplate = ref('品牌讲解型')
const digitalScene = ref('极简直播间')
const videoPurposeScene = ref<AvatarPurposeScene>(props.purposeScene)
const isProductIntroScene = computed(() => props.purposeScene === '产品介绍数字人')
const subtitleSettingsEnabled = ref(true)
const subtitleMode = ref<'default' | 'brand' | 'digital'>('default')
const subtitleFontSizeSlider = ref('42')
const subtitleOffsetYSlider = ref('64')
const subtitleAlign = ref<(typeof subtitleAlignOptions)[number]['value']>('center')
const backgroundMode = ref<'original' | 'image_fill' | 'video_fill'>('original')
const backgroundAssetId = ref<number | null>(null)
const backgroundAssetName = ref('')
const backgroundAssetUrl = ref('')
const effectiveBackgroundMode = computed<'original' | 'image_fill' | 'video_fill'>(() => {
  if ((backgroundMode.value === 'image_fill' || backgroundMode.value === 'video_fill') && !backgroundAssetUrl.value.trim()) {
    return 'original'
  }
  return backgroundMode.value
})

const purposeLocked = computed(() => Boolean(props.purposeLocked))
const sceneFlowConfig = computed(() => getAvatarSceneFlowConfig(videoPurposeScene.value))
const sceneStepIndexMap = computed(() => {
  const map = new Map<AvatarStepKey, number>()
  sceneFlowConfig.value.steps.forEach((key, index) => {
    map.set(key, index + 1)
  })
  return map
})
const effectivePageTitle = computed(() => props.pageTitle || sceneFlowConfig.value.pageTitle)
const effectivePageSubtitle = computed(() => props.pageSubtitle || sceneFlowConfig.value.pageSubtitle)
const sceneRequiresAudio = computed(() => sceneFlowConfig.value.requiresAudio)
const isModelScene = computed(() => videoPurposeScene.value === '模特数字人')
const draftSummaries = computed<DraftSummary[]>(() => (
  draftLibraryItems.value.map((item) => ({
    id: item.draft_id,
    title: item.title || '未命名草稿',
    status: item.status,
    updatedAt: item.updated_at,
    scene: sceneCodeToPurposeScene(item.scene_code),
  }))
))
const currentSceneDraftCount = computed(() => (
  draftSummaries.value.filter((item) => item.scene === props.purposeScene).length
))
const showFlowColumn = computed(() => (
  isStepVisible('extract')
  || isStepVisible('rewrite')
  || isStepVisible('voice')
))
const showStudioColumn = computed(() => (
  isStepVisible('avatar')
  || isStepVisible('model_prompt')
))
const visibleColumnCount = computed(() => (
  Number(showFlowColumn.value)
  + Number(showStudioColumn.value)
  + 1
))
const gridLayoutClass = computed(() => {
  if (visibleColumnCount.value <= 1) return 'grid-layout-single'
  if (visibleColumnCount.value === 2) return 'grid-layout-double'
  return 'grid-layout-triple'
})
const productImageAssets = computed(() => productAssets.value.filter((item) => item.assetType !== 'video'))
const selectedWhiteAsset = computed(() => productAssets.value.find((item) => item.id === selectedWhiteImageId.value) || null)
const selectedWearAsset = computed(() => productAssets.value.find((item) => item.id === selectedWearImageId.value) || null)
const currentDraftApiBase = computed(() => (
  isProductIntroScene.value ? '/api/v1/avatar-product-drafts' : '/api/v1/avatar-sales-drafts'
))
const currentDraftSceneStateKey = computed(() => (
  isProductIntroScene.value ? 'product_scene' : 'sales_scene'
))

function isStepVisible(stepKey: AvatarStepKey) {
  return sceneStepIndexMap.value.has(stepKey)
}

function stepNumber(stepKey: AvatarStepKey) {
  const index = sceneStepIndexMap.value.get(stepKey) || 0
  return String(index).padStart(2, '0')
}

function stepTitle(stepKey: AvatarStepKey) {
  return sceneFlowConfig.value.stepTitles?.[stepKey] || stepKey
}

function isValidPurposeScene(value: string): value is AvatarPurposeScene {
  return value in purposeSceneRouteMap
}

function sceneCodeToPurposeScene(sceneCode?: string | null): AvatarPurposeScene {
  return sceneCode && sceneCodePurposeMap[sceneCode]
    ? sceneCodePurposeMap[sceneCode]
    : props.purposeScene
}

function hasTextContent(value: unknown) {
  return typeof value === 'string' && value.trim().length > 0
}

function openInstructionDialog() {
  showInstructionDialog.value = true
}

function closeInstructionDialog() {
  showInstructionDialog.value = false
}

function formatDraftTime(value: string) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function inferDraftSceneFromLegacyData(draft: LegacyDraftListItem | CreationDraftRead): AvatarPurposeScene {
  const digitalParams = draft.digital_human_params || {}
  const clipParams = draft.clip_params || {}
  const voiceParams = draft.voice_params || {}
  const transcript = draft.transcript || {}
  const explicitPurpose = String(digitalParams.video_purpose || '').trim()

  const hasTalkSignals = (
    hasTextContent((transcript as Record<string, unknown>).text)
    || hasTextContent(draft.extracted_copy)
    || hasTextContent(draft.rewritten_copy)
    || hasTextContent(voiceParams.audio_url)
    || hasTextContent(voiceParams.local_audio_url)
    || hasTextContent(voiceParams.source_audio_url)
    || String(clipParams.template_mode || '') === 'talking_head'
  )

  if (explicitPurpose === '口播数字人') {
    return '口播数字人'
  }
  if (explicitPurpose === '模特数字人' && hasTalkSignals) {
    return '口播数字人'
  }
  if (explicitPurpose && isValidPurposeScene(explicitPurpose)) {
    return explicitPurpose
  }
  if (hasTalkSignals) {
    return '口播数字人'
  }
  return props.purposeScene
}

function shouldUseLegacyTalkDraftFallback() {
  return props.purposeScene === '口播数字人'
}

function mapLegacyDraftToIndexItem(draft: LegacyDraftListItem): AvatarDraftIndexRead {
  const scene = inferDraftSceneFromLegacyData(draft)
  return {
    draft_id: draft.draft_id,
    user_id: 0,
    scene_code: purposeSceneCodeMap[scene],
    title: draft.title,
    status: draft.status,
    current_step_code: null,
    progress: null,
    created_at: draft.updated_at,
    updated_at: draft.updated_at,
  }
}

async function loadLegacyDraftLibraryFallback() {
  const data = await request<CreationDraftListResponse>('/api/v1/creation-drafts?limit=20&offset=0')
  const items = (data.items || [])
    .filter((draft) => inferDraftSceneFromLegacyData(draft) === props.purposeScene)
    .map(mapLegacyDraftToIndexItem)
  draftLibraryItems.value = items
}

async function ensureDraftSceneMatchesCurrentPage(id: string) {
  let draftScene: AvatarPurposeScene | null = null
  try {
    const summary = await request<AvatarDraftIndexRead>(`/api/v1/avatar-drafts/${id}`)
    draftScene = sceneCodeToPurposeScene(summary.scene_code)
    if (draftScene !== props.purposeScene && shouldUseLegacyTalkDraftFallback()) {
      const legacyDraft = await request<CreationDraftRead>(`/api/v1/creation-drafts/${id}`)
      const inferredLegacyScene = inferDraftSceneFromLegacyData(legacyDraft)
      if (inferredLegacyScene === props.purposeScene) {
        draftScene = inferredLegacyScene
      }
    }
  } catch (error) {
    if (!shouldUseLegacyTalkDraftFallback()) {
      throw error
    }
    const legacyDraft = await request<CreationDraftRead>(`/api/v1/creation-drafts/${id}`)
    draftScene = inferDraftSceneFromLegacyData(legacyDraft)
  }

  if (!draftScene) {
    return true
  }
  if (draftScene === props.purposeScene) {
    return true
  }

  await router.replace({
    path: purposeSceneRouteMap[draftScene],
    query: {
      ...route.query,
      draftId: id,
    },
  })
  return false
}
const clipTemplate = ref<'talking_head' | 'picture_in_picture'>('talking_head')
const titleTemplate = ref<(typeof titleTemplateOptions)[number]['value']>('none')
const selectedClipTemplate = ref<string>('manual_subtitle')
const clipVideoTitle = ref('')
const overlaySubtitle = ref('')
const overlayTag = ref('')
const bgmMode = ref<'none' | 'uploaded'>('none')
const bgmAssetUrl = ref('')
const voiceVolumeSlider = ref('50')
const bgmVolumeSlider = ref('30')
const persistedClipParams = ref<Record<string, unknown>>({})
const clippingVideo = ref(false)
const clipStylePreviewExpanded = ref(false)
const clipRenderStage = ref('')
const clippedPreviewUrl = ref('')
const clipBlobUrl = ref<string | null>(null)
const showSubtitleSettings = ref(false)
const showClipTemplateLibrary = ref(false)
const showBackgroundLibrary = ref(false)
const clipTemplateCreatorOpen = ref(false)
const showTemplateBgmLibrary = ref(false)
const backgroundAssetsLoading = ref(false)
const backgroundAssets = ref<BackgroundAssetRead[]>([])
const clipTemplatesLoading = ref(false)
const savingClipTemplate = ref(false)
const customClipRenderConfig = ref<ClipRenderConfig | null>(null)
const clipTemplateCoverUploadInput = ref<HTMLInputElement | null>(null)
const clipTemplateCoverUploading = ref(false)
const productKeyword = ref('')
const productsLoading = ref(false)
const productList = ref<BrandProductCard[]>([])
const selectedProductId = ref('')
const selectedProductProfile = ref<BrandProfile | null>(null)
const productAssets = ref<VisualAssetItem[]>([])
const selectedWhiteImageId = ref('')
const selectedWearImageId = ref('')
const productAssetPickerKind = ref<'white' | 'wear' | null>(null)
const salesSceneImageInput = ref<HTMLInputElement | null>(null)
const salesSceneImageUploading = ref(false)
const salesSceneImageUrl = ref('')
const salesImageCount = ref(4)
const salesAspectRatio = ref('3:4')
const salesExtraRequirements = ref('')
const fusionTaskId = ref('')
const fusionTaskStatus = ref('')
const fusionImages = ref<GalleryImageItem[]>([])
const selectedFusionImageUrl = ref('')
const selectedGalleryImageUrls = ref<string[]>([])
const productCollageImageUrl = ref('')
const fusionGenerating = ref(false)
const fusionPreviewImage = ref<GalleryImageItem | null>(null)
let fusionTaskTimer: ReturnType<typeof setTimeout> | null = null
const finalizedFusionTaskNo = ref('')
let instructionGenerationRunId = 0

const clipTemplateTitleModes = [
  { value: 'none', label: '不加标题', description: '只保留字幕层' },
  { value: 'double', label: '主副标题', description: '标题与副标题同显' },
  { value: 'badge', label: '标题加角标', description: '标题与角标同显' },
  { value: 'bottom', label: '底栏标题', description: '标题落在底部' },
] as const

const clipTemplateSubtitleModes = [
  { value: 'clean', label: '无底白字', description: '适合通用口播' },
  { value: 'outline', label: '高对比字幕', description: '背景复杂也清晰' },
  { value: 'highlight', label: '重点词底色', description: '突出信息点' },
  { value: 'double', label: '双行节奏', description: '适合快节奏' },
] as const

const clipTemplateDraft = reactive({
  id: '',
  name: '未命名模板',
  coverAdded: false,
  coverUrl: '',
  titleMode: 'none',
  titleSubtitleText: '这里是副标题',
  titleAlign: 'top-left',
  titleFont: 'default',
  titleSize: 24,
  titleOffsetX: 0,
  titleOffsetY: 0,
  titleSubtitleSize: 13,
  badgeFont: 'default',
  badgeText: '标签',
  badgeSize: 12,
  badgeOffsetX: 0,
  badgeOffsetY: 0,
  bgmVolume: 20,
  subtitleMode: 'clean',
  subtitleAlign: 'center',
  subtitleFont: 'default',
  subtitleSize: 15,
  subtitleOffsetX: 0,
  subtitleOffsetY: 0,
  subtitleDoubleLine: false,
})

const userClipTemplateCards = ref<Array<{
  templateId: number
  value: string
  code: string
  label: string
  description: string
  titleTemplate: string
  subtitleMode: 'default' | 'brand' | 'digital'
  subtitleFontSize: number
  subtitleOffsetY: number
  subtitleAlign: 'left' | 'center' | 'right'
  renderConfig: ClipRenderConfig
  thumbnailUrl?: string | null
  editorConfig?: Record<string, unknown>
}>>([])

const salesVideoResolutionCandidates = [
  { width: 3072, height: 2048, aspectRatio: '3:2', resolution: '3072x2048 (横屏)' },
  { width: 2048, height: 3072, aspectRatio: '2:3', resolution: '2048x3072 (竖屏)' },
  { width: 640, height: 960, aspectRatio: '2:3', resolution: '640x960 (2:3) (竖屏)' },
  { width: 960, height: 640, aspectRatio: '3:2', resolution: '960x640 (3:2) (横屏)' },
  { width: 832, height: 1216, aspectRatio: '13:19', resolution: '832x1216 (13:19) (竖屏)' },
  { width: 1216, height: 832, aspectRatio: '19:13', resolution: '1216x832 (19:13) (横屏)' },
  { width: 1024, height: 1536, aspectRatio: '2:3', resolution: '1024x1536 (2:3) (竖屏)' },
  { width: 1536, height: 1024, aspectRatio: '3:2', resolution: '1536x1024 (3:2) (横屏)' },
  { width: 1280, height: 720, aspectRatio: '16:9', resolution: '1280x720 (16:9) (横屏)' },
  { width: 1920, height: 1080, aspectRatio: '16:9', resolution: '1920x1080 (16:9) (横屏)' },
  { width: 720, height: 1280, aspectRatio: '9:16', resolution: '720x1280 (9:16) (竖屏)' },
  { width: 1080, height: 1920, aspectRatio: '9:16', resolution: '1080x1920 (9:16) (竖屏)' },
  { width: 1344, height: 768, aspectRatio: '7:4', resolution: '1344x768 (7:4) (横屏)' },
  { width: 768, height: 1344, aspectRatio: '4:7', resolution: '768x1344 (4:7) (竖屏)' },
  { width: 1152, height: 896, aspectRatio: '9:7', resolution: '1152x896 (9:7) (横屏)' },
  { width: 896, height: 1152, aspectRatio: '7:9', resolution: '896x1152 (7:9) (竖屏)' },
  { width: 480, height: 832, aspectRatio: '3:5.2', resolution: '480x832 (3:5.2) (竖屏)' },
  { width: 832, height: 480, aspectRatio: '5.2:3', resolution: '832x480 (5.2:3) (横屏)' },
  { width: 480, height: 854, aspectRatio: '9:16', resolution: '480x854 (9:16) (竖屏)' },
  { width: 854, height: 480, aspectRatio: '16:9', resolution: '854x480 (16:9) (横屏)' },
  { width: 512, height: 512, aspectRatio: '1:1', resolution: '512x512 (1:1) (方形)' },
  { width: 768, height: 768, aspectRatio: '1:1', resolution: '768x768 (1:1) (方形)' },
  { width: 1024, height: 1024, aspectRatio: '1:1', resolution: '1024x1024 (1:1) (方形)' },
  { width: 512, height: 768, aspectRatio: '2:3', resolution: '512x768 (2:3) (竖屏)' },
  { width: 768, height: 512, aspectRatio: '3:2', resolution: '768x512 (3:2) (横屏)' },
  { width: 512, height: 896, aspectRatio: '4:7', resolution: '512x896 (4:7) (竖屏)' },
  { width: 896, height: 512, aspectRatio: '7:4', resolution: '896x512 (7:4) (横屏)' },
] as const

const voiceSpeed = computed(() => 0.5 + (Number(voiceSpeedSlider.value) / 100) * 1.5)
const voiceSimilarity = computed(() => Number(voiceSimilaritySlider.value) / 100)
const voiceVolume = computed(() => Number(voiceVolumeSlider.value) / 50)
const bgmVolume = computed(() => Number(bgmVolumeSlider.value) / 100)
const subtitleFontSize = computed(() => Math.max(28, Math.min(64, Number(subtitleFontSizeSlider.value) || 42)))
const subtitleOffsetY = computed(() => Math.max(24, Math.min(180, Number(subtitleOffsetYSlider.value) || 64)))
const backgroundAssetLabel = computed(() => {
  if (backgroundMode.value === 'original') return '直接保留当前数字人视频的原始背景'
  if (backgroundAssetName.value.trim()) {
    return `当前已选择：${backgroundAssetName.value}`
  }
  return backgroundAssetUrl.value
    ? '已上传背景素材，剪辑时会作为底层全屏背景'
    : backgroundMode.value === 'video_fill'
      ? '请上传背景视频，系统会自动裁成竖屏并按时长对齐'
      : '请上传背景图片，系统会自动裁成竖屏背景'
})
const filteredBackgroundAssets = computed(() => (
  backgroundAssets.value.filter((item) => {
    if (backgroundMode.value === 'image_fill') return item.media_type === 'image'
    if (backgroundMode.value === 'video_fill') return item.media_type === 'video'
    return true
  })
))
const officialBackgroundAssets = computed(() => (
  filteredBackgroundAssets.value.filter((item) => item.source_type === 'official')
))
const userBackgroundAssets = computed(() => (
  filteredBackgroundAssets.value.filter((item) => item.source_type !== 'official')
))
const bgmAssetLabel = computed(() => {
  return bgmAssetUrl.value ? '已选择背景音乐，剪辑时会按音量混音' : '当前不混入背景音乐'
})
const visibleClipTemplateCards = computed(() => [
  ...clipTemplateOptions,
  ...userClipTemplateCards.value,
])
const selectedTitleTemplateOption = computed(() => (
  titleTemplateOptions.find((item) => item.value === titleTemplate.value) ?? titleTemplateOptions[0]
))
const selectedClipTemplateOption = computed(() => (
  visibleClipTemplateCards.value.find((item) => item.value === selectedClipTemplate.value) ?? clipTemplateOptions[0]
))
function titleTemplateSupportMeta(templateCode: string) {
  return titleTemplateOptions.find((item) => item.value === templateCode) ?? titleTemplateOptions[0]
}

function renderTitleModeSupportsSubtitle(mode: unknown) {
  return ['double', 'badge', 'bottom'].includes(String(mode || '').trim())
}

const selectedTitleTemplateSupportsSubtitle = computed(() => (
  customClipRenderConfig.value?.title?.enabled
    ? renderTitleModeSupportsSubtitle(customClipRenderConfig.value.title?.mode)
    : titleTemplateSupportMeta(String(selectedClipTemplateOption.value.titleTemplate || 'none')).supportsSubtitle
))
const selectedTitleTemplateSupportsTag = computed(() => (
  customClipRenderConfig.value?.title?.enabled
    ? String(customClipRenderConfig.value.title?.mode || '') === 'badge'
    : titleTemplateSupportMeta(String(selectedClipTemplateOption.value.titleTemplate || 'none')).supportsTag
))
const selectedTitleTemplateDescription = computed(() => (
  !subtitleSettingsEnabled.value
    ? String(selectedClipTemplateOption.value.description || titleTemplateSupportMeta(String(selectedClipTemplateOption.value.titleTemplate || 'none')).description)
    : selectedTitleTemplateOption.value.description
))
const clipTemplateRuntimeFormVisible = computed(() => (
  !subtitleSettingsEnabled.value && (selectedTitleTemplateSupportsSubtitle.value || selectedTitleTemplateSupportsTag.value)
))
const selectedTitleTemplatePresetLabel = computed(() => {
  const modeMap: Record<(typeof subtitleModeOptions)[number]['value'], string> = {
    default: '默认字幕',
    brand: '品牌字幕',
    digital: '数字风字幕',
  }
  return subtitleSettingsEnabled.value
    ? modeMap[subtitleMode.value]
    : selectedClipTemplateOption.value.label
})
const selectedTitleTemplatePresetCode = computed(() => {
  const modeMap: Record<(typeof subtitleModeOptions)[number]['value'], string> = {
    default: 'T1',
    brand: 'T2',
    digital: 'T3',
  }
  return subtitleSettingsEnabled.value ? modeMap[subtitleMode.value] : selectedClipTemplateOption.value.code
})

function clipTemplateCardThumbnail(item: { thumbnailUrl?: string | null }) {
  return item.thumbnailUrl || ''
}

function isUserClipTemplateCard(item: { value: string }) {
  return item.value.startsWith('user_')
}

const autoClipVideoTitle = computed(() => {
  const titleFromContent = (extractResult.value?.content_info?.title || '').trim()
  if (titleFromContent) return titleFromContent
  const preferred = rewrittenCopy.value.trim() || sourceCopy.value.trim()
  if (!preferred) return ''
  return preferred.slice(0, 30)
})

const draftTitle = computed(() => autoClipVideoTitle.value || '提取文案后，可继续生成视频标题')

const resolvedClipVideoTitle = computed(() => {
  const manual = clipVideoTitle.value.trim()
  if (manual) return manual
  return autoClipVideoTitle.value || '提取文案后，可继续生成视频标题'
})

const previewTitleText = computed(() => resolvedClipVideoTitle.value || '这里是标题')
const previewSubtitleText = computed(() => overlaySubtitle.value.trim() || '这里是副标题')
const previewTagText = computed(() => overlayTag.value.trim() || '标签')
const clipTemplatePreviewTitleText = computed(() => previewTitleText.value)
const clipTemplatePreviewSubtitleText = computed(() => clipTemplateDraft.titleSubtitleText.trim() || previewSubtitleText.value)
const clipTemplatePreviewBadgeText = computed(() => clipTemplateDraft.badgeText.trim() || previewTagText.value)
const previewCaptionText = computed(() => {
  const raw = rewrittenCopy.value.trim() || sourceCopy.value.trim() || '这里显示字幕预览效果，方便判断是否遮挡人物区域。'
  return raw.replace(/\s+/g, ' ').slice(0, 36)
})
const previewVideoUrl = computed(() => {
  const direct = generatedVideoUrl.value.trim()
  if (direct) return direct
  return generatedVideoSourceUrl.value.trim()
})
const previewBaseImageUrl = computed(() => {
  if (previewFrameDataUrl.value) return previewFrameDataUrl.value
  if (previewVideoUrl.value) return ''
  return digitalHumanImageUrl.value || ''
})
const previewStageEmptyMessage = computed(() => {
  if (previewFrameLoading.value && previewVideoUrl.value) return '正在从数字人成片提取预览帧…'
  if (previewVideoUrl.value) return '数字人成片预览帧暂时不可用，请稍后重试。'
  return '先生成数字人视频，这里会显示当前字幕样式。'
})
const previewCanvasSize = computed(() => {
  const width = previewFrameWidth.value || digitalHumanVideoWidth.value || digitalHumanImageWidth.value || 720
  const height = previewFrameHeight.value || digitalHumanVideoHeight.value || digitalHumanImageHeight.value || 1280
  return { width: Math.max(1, width), height: Math.max(1, height) }
})
const activeClipRenderConfig = computed<ClipRenderConfig>(() => (
  customClipRenderConfig.value && !subtitleSettingsEnabled.value
    ? mergeClipRenderConfigWithRuntime(customClipRenderConfig.value)
    : buildClipRenderConfigFromRuntime()
))

function cloneRenderConfig(config: ClipRenderConfig): ClipRenderConfig {
  return JSON.parse(JSON.stringify(config)) as ClipRenderConfig
}

function scaleNumber(value: unknown, fallback: number, scale: number) {
  const numeric = Number(value)
  return (Number.isFinite(numeric) ? numeric : fallback) * scale
}

function scalePreviewSection(section: Record<string, unknown> | undefined, scaleX: number, scaleY: number, scaleFont: number) {
  if (!section) return
  for (const field of ['x', 'badgeX']) {
    if (field in section) section[field] = scaleNumber(section[field], 0, scaleX)
  }
  for (const field of ['y', 'badgeY']) {
    if (field in section) section[field] = scaleNumber(section[field], 0, scaleY)
  }
  for (const field of ['fontSize', 'subtitleFontSize', 'badgeFontSize']) {
    if (field in section) section[field] = Math.max(8, scaleNumber(section[field], 24, scaleFont))
  }
}

function scaleRenderConfigForPreview(config: ClipRenderConfig, width: number, height: number): ClipRenderConfig {
  const designWidth = Math.max(1, Number(config.canvas?.width) || width)
  const designHeight = Math.max(1, Number(config.canvas?.height) || height)
  if (designWidth === width && designHeight === height) return config
  const scaled = cloneRenderConfig(config)
  const scaleX = width / designWidth
  const scaleY = height / designHeight
  const scaleFont = Math.min(scaleX, scaleY)
  scalePreviewSection(scaled.title as unknown as Record<string, unknown>, scaleX, scaleY, scaleFont)
  scalePreviewSection(scaled.subtitle as unknown as Record<string, unknown>, scaleX, scaleY, scaleFont)
  scaled.canvas = {
    ...scaled.canvas,
    width,
    height,
    sourceWidth: designWidth,
    sourceHeight: designHeight,
  }
  return scaled
}

const previewRenderConfig = computed(() => {
  const { width, height } = previewCanvasSize.value
  return scaleRenderConfigForPreview(activeClipRenderConfig.value, width, height)
})

function previewTextAnchor(align: string) {
  if (align === 'center') return 'middle'
  if (align === 'right') return 'end'
  return 'start'
}

function previewAlignedX(align: string, x: number, width: number) {
  if (align === 'center') return width / 2 + x
  if (align === 'right') return width - 36 + x
  return 36 + x
}

function previewCssColor(color: string) {
  const trimmed = String(color || '').trim()
  if (!trimmed) return 'transparent'
  if (trimmed.includes('@')) {
    const [base, rawOpacity] = trimmed.split('@')
    const opacity = Math.max(0, Math.min(1, Number(rawOpacity)))
    if (base === 'black') return `rgb(0 0 0 / ${opacity})`
    if (base === 'white') return `rgb(255 255 255 / ${opacity})`
    if (/^#([0-9a-fA-F]{6})$/.test(base)) {
      const hex = /^#([0-9a-fA-F]{6})$/.exec(base)
      if (hex) {
        const raw = hex[1]
        const r = Number.parseInt(raw.slice(0, 2), 16)
        const g = Number.parseInt(raw.slice(2, 4), 16)
        const b = Number.parseInt(raw.slice(4, 6), 16)
        return `rgb(${r} ${g} ${b} / ${opacity})`
      }
    }
  }
  return trimmed
}

function previewSubtitleBoxColor(mode: string, configured?: string | null) {
  if (configured) return previewCssColor(configured)
  if (mode === 'outline') return 'rgb(255 255 255 / 0.90)'
  if (mode === 'highlight') return 'rgb(255 240 168 / 0.95)'
  if (mode === 'double') return 'rgb(12 30 61 / 0.82)'
  return 'transparent'
}

function previewSubtitleColor(mode: string, configured?: string | null) {
  if (configured) return configured
  return mode === 'outline' || mode === 'highlight' ? '#0F172A' : '#FFFFFF'
}

const renderPreviewTitle = computed(() => {
  const config = previewRenderConfig.value
  const title = config.title
  if (!title?.enabled || !title.text) return null
  const width = previewCanvasSize.value.width
  const align = title.align || 'center'
  const x = previewAlignedX(align, Number(title.x) || 0, width)
  const y = Math.max(0, Number(title.y) || 0)
  const fontSize = Math.max(8, Number(title.fontSize) || 24)
  const subtitleSize = Math.max(8, Number(title.subtitleFontSize) || Math.round(fontSize * 0.58))
  return {
    anchor: previewTextAnchor(align),
    x,
    y,
    fontSize,
    subtitleSize,
    text: String(title.text).slice(0, 32),
    subtitle: String(title.subtitle || '').slice(0, 32),
    color: title.color || '#FFFFFF',
    subtitleColor: title.subtitleColor || '#FF9A32',
  }
})

const renderPreviewSubtitle = computed(() => {
  const config = previewRenderConfig.value
  const subtitle = config.subtitle
  if (!subtitle?.enabled) return null
  const width = previewCanvasSize.value.width
  const mode = subtitle.mode || 'clean'
  const align = subtitle.align || 'center'
  const fontSize = Math.max(8, Number(subtitle.fontSize) || 24)
  const text = previewCaptionText.value.slice(0, 32)
  const textWidth = Math.max(fontSize * 2.2, text.length * fontSize * 0.92)
  const paddingX = Math.max(12, Math.round(fontSize * 0.36))
  const paddingY = Math.max(8, Math.round(fontSize * 0.22))
  const x = previewAlignedX(align, Number(subtitle.x) || 0, width)
  const boxWidth = Math.min(width - 24, textWidth + paddingX * 2)
  const boxX = align === 'center'
    ? x - boxWidth / 2
    : align === 'right'
      ? x - boxWidth
      : x
  const y = Math.max(0, Number(subtitle.y) || 0)
  const boxColor = previewSubtitleBoxColor(mode, subtitle.background)
  const showBox = boxColor !== 'transparent'
  return {
    anchor: previewTextAnchor(align),
    x,
    y,
    fontSize,
    lineHeight: Math.max(fontSize + 10, Math.round(fontSize * 1.28)),
    text,
    color: previewSubtitleColor(mode, subtitle.color),
    boxColor,
    borderColor: previewCssColor(subtitle.borderColor || 'black@0.35'),
    borderWidth: showBox ? Math.max(0, Number(subtitle.borderWidth) || 0) : 0,
    showBox,
    boxX: Math.max(6, Math.min(width - boxWidth - 6, boxX)),
    boxY: Math.max(0, y - paddingY),
    boxWidth,
    boxHeight: fontSize * 1.32 + paddingY * 2,
  }
})

const clipTemplateDraftBackgroundClass = computed(() => {
  if (backgroundMode.value === 'image_fill') return 'clip-template-cover-bg--image'
  if (backgroundMode.value === 'video_fill') return 'clip-template-cover-bg--video'
  return 'clip-template-cover-bg--original'
})
const clipTemplateTitlePreviewStyle = computed(() => ({
  transform: `translate(${clipTemplateDraft.titleOffsetX}px, ${clipTemplateDraft.titleOffsetY}px)`,
  fontFamily: clipTemplateDraft.titleFont === 'serif' ? '"Songti SC", "STSong", serif' : '"Noto Sans SC", "PingFang SC", sans-serif',
  fontWeight: clipTemplateDraft.titleFont === 'bold' ? '800' : '700',
  letterSpacing: clipTemplateDraft.titleFont === 'brand' ? '0.02em' : '0',
  '--clip-title-size': `${clipTemplateDraft.titleSize}px`,
  '--clip-subtitle-size': `${clipTemplateDraft.titleSubtitleSize}px`,
}))
const clipTemplateBadgePreviewStyle = computed(() => ({
  transform: `translate(${clipTemplateDraft.badgeOffsetX}px, ${clipTemplateDraft.badgeOffsetY}px)`,
  fontSize: `${clipTemplateDraft.badgeSize}px`,
  fontFamily: clipTemplateDraft.badgeFont === 'serif' ? '"Songti SC", "STSong", serif' : '"Noto Sans SC", "PingFang SC", sans-serif',
  fontWeight: clipTemplateDraft.badgeFont === 'bold' ? '800' : '700',
  letterSpacing: clipTemplateDraft.badgeFont === 'brand' ? '0.02em' : '0',
}))
const clipTemplateSubtitlePreviewStyle = computed(() => ({
  transform: `translate(${clipTemplateDraft.subtitleOffsetX}px, ${clipTemplateDraft.subtitleOffsetY}px)`,
  fontSize: `${clipTemplateDraft.subtitleSize}px`,
  fontFamily: clipTemplateDraft.subtitleFont === 'serif' ? '"Songti SC", "STSong", serif' : '"Noto Sans SC", "PingFang SC", sans-serif',
  fontWeight: clipTemplateDraft.subtitleFont === 'bold' ? '800' : '700',
  letterSpacing: clipTemplateDraft.subtitleFont === 'brand' ? '0.02em' : '0',
}))
const selectedVoiceOption = computed(() => (
  voiceOptions.value.find((item) => String(item.id) === selectedVoiceAssetId.value) ?? null
))
const systemVoiceOptions = computed(() => (
  voiceOptions.value.filter((item) => (item.source_type || '') === 'system_builtin')
))
const userVoiceOptions = computed(() => (
  voiceOptions.value.filter((item) => (item.source_type || '') !== 'system_builtin')
))
const selectedCloneVoiceLabel = computed(() => {
  const voice = userVoiceOptions.value.find((item) => String(item.id) === selectedVoiceAssetId.value)
  return voice?.voice_name || '请选择我的音色'
})
const selectedVoiceDescription = computed(() => {
  const voice = selectedVoiceOption.value
  if (!voice) return ''
  const bits = [voice.voice_style, voice.voice_desc].filter(Boolean)
  return bits.join(' · ')
})

function subtitleBackgroundForMode(mode: string) {
  if (mode === 'outline') return 'white@0.90'
  if (mode === 'highlight' || mode === 'brand') return '#FFF0A8@0.95'
  if (mode === 'double' || mode === 'digital') return '#0C1E3D@0.82'
  return ''
}

function subtitleColorForMode(mode: string) {
  return mode === 'outline' || mode === 'highlight' || mode === 'brand' ? '#0F172A' : '#FFFFFF'
}

function normalizedTitleMode() {
  if (titleTemplate.value === 'none') return 'none'
  if (titleTemplate.value === 'headline_tag') return 'badge'
  if (titleTemplate.value === 'headline_box') return 'double'
  if (titleTemplate.value === 'headline_white') return 'single'
  return 'double'
}

function normalizedTitleAlign(): 'left' | 'center' | 'right' {
  return ['headline_white', 'headline_white_orange', 'headline_box', 'headline_gold'].includes(titleTemplate.value)
    ? 'center'
    : 'left'
}

function buildClipRenderConfigFromRuntime(): ClipRenderConfig {
  const titleMode = normalizedTitleMode()
  const titleEnabled = !subtitleSettingsEnabled.value && titleMode !== 'none'
  const subtitleY = Math.max(40, 1280 - subtitleOffsetY.value - subtitleFontSize.value - 18)
  return {
    version: 1,
    canvas: {
      width: 720,
      height: 1280,
      fps: 30,
      aspectMode: 'source',
    },
    background: {
      mode: effectiveBackgroundMode.value,
      assetUrl: backgroundAssetUrl.value.trim() || null,
      assetName: backgroundAssetName.value.trim() || null,
      fit: 'cover',
    },
    title: {
      enabled: titleEnabled,
      mode: titleMode,
      text: previewTitleText.value,
      subtitle: previewSubtitleText.value,
      badge: previewTagText.value,
      align: normalizedTitleAlign(),
      x: 0,
      y: titleMode === 'bottom' ? 930 : 82,
      fontSize: 46,
      subtitleFontSize: 30,
      badgeFontSize: 22,
      fontWeight: 800,
      color: titleTemplate.value === 'headline_gold' ? '#F4C542' : '#FFFFFF',
      subtitleColor: titleTemplate.value === 'headline_white_orange' || titleTemplate.value === 'headline_tag' ? '#FF9A32' : '#FFFFFF',
      badgeColor: '#FFFFFF',
      borderColor: 'black@0.50',
      box: titleTemplate.value === 'headline_box',
      boxColor: 'black@0.38',
      badgeX: 0,
      badgeY: 0,
    },
    subtitle: {
      enabled: true,
      mode: subtitleMode.value,
      align: subtitleAlign.value,
      x: 0,
      y: subtitleY,
      fontSize: subtitleFontSize.value,
      fontWeight: subtitleMode.value === 'default' ? 600 : 800,
      color: subtitleColorForMode(subtitleMode.value),
      background: subtitleBackgroundForMode(subtitleMode.value),
      borderColor: 'black@0.35',
      borderWidth: subtitleMode.value === 'default' ? 0 : 1,
      doubleLine: subtitleMode.value === 'digital',
    },
    audio: {
      voiceVolume: voiceVolume.value,
      bgmUrl: bgmAssetUrl.value.trim() || null,
      bgmVolume: bgmVolume.value,
    },
  }
}

function buildClipTemplateDraftRenderConfig(): ClipRenderConfig {
  const draftTitleMode = clipTemplateDraft.titleMode
  const titleAlign = clipTemplateDraft.titleAlign.includes('center')
    ? 'center'
    : clipTemplateDraft.titleAlign.includes('right')
      ? 'right'
      : 'left'
  const subtitleModeForRender = clipTemplateDraft.subtitleMode === 'highlight'
    ? 'highlight'
    : clipTemplateDraft.subtitleMode === 'outline'
      ? 'outline'
      : clipTemplateDraft.subtitleMode === 'double'
        ? 'double'
        : 'clean'
  return {
    ...buildClipRenderConfigFromRuntime(),
    title: {
      ...buildClipRenderConfigFromRuntime().title,
      enabled: draftTitleMode !== 'none',
      mode: draftTitleMode,
      text: previewTitleText.value,
      subtitle: clipTemplateDraft.titleSubtitleText.trim() || previewSubtitleText.value,
      badge: clipTemplateDraft.badgeText.trim() || previewTagText.value,
      align: titleAlign,
      x: clipTemplateDraft.titleOffsetX,
      y: draftTitleMode === 'bottom' ? 920 + clipTemplateDraft.titleOffsetY : 82 + clipTemplateDraft.titleOffsetY,
      fontSize: Math.round(clipTemplateDraft.titleSize * 1.8),
      subtitleFontSize: Math.round(clipTemplateDraft.titleSubtitleSize * 1.8),
      badgeFontSize: Math.round(clipTemplateDraft.badgeSize * 1.7),
      fontWeight: clipTemplateDraft.titleFont === 'default' ? 700 : 800,
      badgeX: clipTemplateDraft.badgeOffsetX,
      badgeY: clipTemplateDraft.badgeOffsetY,
    },
    subtitle: {
      ...buildClipRenderConfigFromRuntime().subtitle,
      mode: subtitleModeForRender,
      align: clipTemplateDraft.subtitleAlign as 'left' | 'center' | 'right',
      x: clipTemplateDraft.subtitleOffsetX,
      y: Math.max(40, 1280 - 92 - Math.round(clipTemplateDraft.subtitleSize * 1.9) + clipTemplateDraft.subtitleOffsetY),
      fontSize: Math.round(clipTemplateDraft.subtitleSize * 1.9),
      fontWeight: clipTemplateDraft.subtitleFont === 'default' ? 600 : 800,
      color: subtitleColorForMode(subtitleModeForRender),
      background: subtitleBackgroundForMode(subtitleModeForRender),
      doubleLine: clipTemplateDraft.subtitleDoubleLine || subtitleModeForRender === 'double',
    },
    audio: {
      voiceVolume: voiceVolume.value,
      bgmUrl: bgmAssetUrl.value.trim() || null,
      bgmVolume: Math.max(0, Math.min(1, clipTemplateDraft.bgmVolume / 100)),
    },
  }
}

function mergeClipRenderConfigWithRuntime(config: ClipRenderConfig): ClipRenderConfig {
  return {
    ...config,
    background: {
      ...config.background,
      mode: effectiveBackgroundMode.value,
      assetUrl: backgroundAssetUrl.value.trim() || config.background.assetUrl || null,
      assetName: backgroundAssetName.value.trim() || config.background.assetName || null,
    },
    title: {
      ...config.title,
      text: resolvedClipVideoTitle.value || config.title.text || previewTitleText.value,
      subtitle: overlaySubtitle.value.trim() || config.title.subtitle || previewSubtitleText.value,
      badge: overlayTag.value.trim() || config.title.badge || previewTagText.value,
    },
    audio: {
      ...config.audio,
      voiceVolume: voiceVolume.value,
      bgmUrl: bgmAssetUrl.value.trim() || config.audio.bgmUrl || null,
      bgmVolume: bgmAssetUrl.value.trim() ? bgmVolume.value : 0,
    },
  }
}

const currentModeLabel = computed(() => {
  if (currentMode.value === 'manual') return '手动模式'
  if (currentMode.value === 'auto') return '自动模式'
  return '批量模式'
})
const digitalHumanTaskStatusLabel = computed(() => {
  if (generatingDigitalHuman.value) return '数字人视频生成中'
  if (digitalHumanTaskStatus.value) return digitalHumanTaskStatus.value
  if (generatedVideoUrl.value) return '已生成'
  return '待生成'
})
const digitalHumanImageMetaLabel = computed(() => {
  if (!digitalHumanImageWidth.value || !digitalHumanImageHeight.value) return ''
  const ratio = digitalHumanImageWidth.value / digitalHumanImageHeight.value
  const orientation = ratio > 1.05 ? '横图' : ratio < 0.95 ? '竖图' : '方图'
  return `${digitalHumanImageWidth.value} x ${digitalHumanImageHeight.value}，${orientation}`
})
const digitalHumanVideoMetaLabel = computed(() => {
  if (!digitalHumanVideoWidth.value || !digitalHumanVideoHeight.value) return ''
  const ratio = digitalHumanVideoWidth.value / digitalHumanVideoHeight.value
  const orientation = ratio > 1.05 ? '横屏' : ratio < 0.95 ? '竖屏' : '方屏'
  return `${digitalHumanVideoWidth.value} x ${digitalHumanVideoHeight.value}，${orientation}`
})
const clipRenderDisabledReason = computed(() => {
  if (!draftId.value) return '请先保存创作草稿'
  if (!generatedVideoUrl.value) return '请先生成数字人成片'
  return ''
})

const detectedPlatform = computed(() => extractResult.value?.parsed_link.platform ?? '')
const activeModelName = computed(() => rewriteResult.value?.model_name || extractResult.value?.model_name || '未调用')
const workflowStatusLabel = computed(() => {
  if (rewrittenCopy.value.trim()) return '文案已改写'
  if (sourceCopy.value.trim()) return '已提取文案'
  return '待生成'
})

const extractMeta = computed(() => {
  const result = extractResult.value
  if (!result) return ''

  const bits: string[] = []
  if (result.content_info?.title) bits.push(`标题：${result.content_info.title}`)
  if (result.content_info?.author_name) bits.push(`作者：${result.content_info.author_name}`)
  if (result.model_name) bits.push(`模型：${result.model_name}`)
  return bits.join(' · ')
})

const rewriteMeta = computed(() => {
  const result = rewriteResult.value
  if (!result) return ''

  const bits: string[] = []
  if (result.instruction) bits.push(`指令：${result.instruction}`)
  if (result.model_name) bits.push(`模型：${result.model_name}`)
  return bits.join(' · ')
})

async function loadProducts() {
  productsLoading.value = true
  try {
    const data = await listBrandProducts({ keyword: productKeyword.value, pageNo: 1, pageSize: 100 })
    productList.value = data.list || []
  } finally {
    productsLoading.value = false
  }
}

async function selectProduct(brandId: string) {
  if (!brandId) {
    selectedProductId.value = ''
    selectedProductProfile.value = null
    productAssets.value = []
    selectedWhiteImageId.value = ''
    selectedWearImageId.value = ''
    return
  }
  selectedProductId.value = brandId
  selectedProductProfile.value = await getBrandProfile(brandId)
  productAssets.value = await getVisualAssets(brandId)
  const firstImage = productImageAssets.value[0]
  selectedWhiteImageId.value = firstImage?.id || ''
  selectedWearImageId.value = productImageAssets.value[1]?.id || firstImage?.id || ''
}

async function handleProductChange() {
  await selectProduct(selectedProductId.value)
}

function selectWhiteAsset(id: string) {
  selectedWhiteImageId.value = id
}

function selectWearAsset(id: string) {
  selectedWearImageId.value = id
}

function openProductAssetPicker(kind: 'white' | 'wear') {
  productAssetPickerKind.value = kind
}

function closeProductAssetPicker() {
  productAssetPickerKind.value = null
}

function confirmProductAssetPick(id: string) {
  if (productAssetPickerKind.value === 'white') selectWhiteAsset(id)
  else if (productAssetPickerKind.value === 'wear') selectWearAsset(id)
  closeProductAssetPicker()
}

function openSalesSceneImageUpload() {
  if (salesSceneImageUploading.value) return
  salesSceneImageInput.value?.click()
}

function buildHeaders() {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = authStore.state.session?.accessToken
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return headers
}

function resolveSubtitleMode(value: unknown): 'default' | 'brand' | 'digital' {
  return value === 'brand' || value === 'digital' ? value : 'default'
}

function previewVideoCandidates(preferred?: string) {
  return [preferred, generatedVideoUrl.value, generatedVideoSourceUrl.value]
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter((item, index, list) => item && list.indexOf(item) === index)
}

async function extractPreviewFrame(preferredVideoUrl?: string) {
  const requestId = ++previewFrameRequestId
  const candidates = previewVideoCandidates(preferredVideoUrl)
  previewFrameLoading.value = true
  previewFrameDataUrl.value = ''
  previewFrameWidth.value = 0
  previewFrameHeight.value = 0
  if (!candidates.length) {
    previewFrameLoading.value = false
    return
  }

  try {
    let lastError: unknown = null
    for (const videoUrl of candidates) {
      try {
        const response = await fetch(videoUrl, { headers: buildHeaders() })
        if (!response.ok) {
          throw new Error(`预览帧拉取失败: ${response.status}`)
        }
        const blob = await response.blob()
        const objectUrl = URL.createObjectURL(blob)
        const frame = await new Promise<{ dataUrl: string; width: number; height: number }>((resolve, reject) => {
          const video = document.createElement('video')
          video.muted = true
          video.playsInline = true
          video.preload = 'auto'
          video.src = objectUrl
          const cleanup = () => {
            video.pause()
            video.removeAttribute('src')
            video.load()
            URL.revokeObjectURL(objectUrl)
          }
          video.onloadedmetadata = () => {
            const targetTime = Math.max(0.1, Math.min(video.duration * 0.35, 1.5))
            video.currentTime = Number.isFinite(targetTime) ? targetTime : 0.1
          }
          video.onseeked = () => {
            const canvas = document.createElement('canvas')
            canvas.width = video.videoWidth || 1080
            canvas.height = video.videoHeight || 1920
            const ctx = canvas.getContext('2d')
            if (!ctx) {
              cleanup()
              reject(new Error('无法创建预览画布'))
              return
            }
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
            cleanup()
            resolve({ dataUrl, width: canvas.width, height: canvas.height })
          }
          video.onerror = () => {
            cleanup()
            reject(new Error('视频预览帧解析失败'))
          }
        })
        if (requestId !== previewFrameRequestId) return
        previewFrameWidth.value = frame.width
        previewFrameHeight.value = frame.height
        previewFrameDataUrl.value = frame.dataUrl
        return
      } catch (error) {
        lastError = error
      }
    }
    throw lastError ?? new Error('视频预览帧解析失败')
  } catch (error) {
    if (requestId !== previewFrameRequestId) return
    console.error('Failed to extract preview frame', error)
    previewFrameDataUrl.value = ''
    previewFrameWidth.value = 0
    previewFrameHeight.value = 0
  } finally {
    if (requestId === previewFrameRequestId) {
      previewFrameLoading.value = false
    }
  }
}

function isPublicHttpMediaUrl(u: string): boolean {
  try {
    const parsed = new URL(u.trim())
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return false
    const h = parsed.hostname.toLowerCase()
    if (!h || h === 'localhost' || h === '127.0.0.1' || h === '::1') return false
    if (h.endsWith('.localhost')) return false
    return true
  } catch {
    return false
  }
}

/** 与主后端 pick_public_asr_media_url_for_clip 一致：优先口播源/合成音频，再成片视频；排除 localhost。 */
function pickPublicMediaForClipAsr(): string | null {
  for (const raw of [generatedAudioUrl.value, generatedAudioSourceUrl.value]) {
    const u = typeof raw === 'string' ? raw.trim() : ''
    if (u && isPublicHttpMediaUrl(u)) return u
  }
  const v = typeof generatedVideoUrl.value === 'string' ? generatedVideoUrl.value.trim() : ''
  if (v && isPublicHttpMediaUrl(v)) return v
  return null
}

async function refreshClippedPreview() {
  clippedPreviewUrl.value = ''
  if (clipBlobUrl.value) {
    URL.revokeObjectURL(clipBlobUrl.value)
    clipBlobUrl.value = null
  }
  const cp = persistedClipParams.value
  const direct = typeof cp.clipped_video_url === 'string' ? cp.clipped_video_url.trim() : ''
  if (direct) {
    clippedPreviewUrl.value = direct
    return
  }
  if (cp.playback_requires_auth && draftId.value) {
    try {
      const path = `${getApiBaseUrl()}${currentDraftApiBase.value}/${draftId.value}/clipped-video`
      const r = await fetch(path, { headers: buildHeaders() })
      if (!r.ok) return
      const blob = await r.blob()
      clipBlobUrl.value = URL.createObjectURL(blob)
      clippedPreviewUrl.value = clipBlobUrl.value
    } catch (error) {
      console.error('Failed to load clipped preview', error)
    }
  }
}

function openSubtitleSettings() {
  if (!previewFrameDataUrl.value && previewVideoUrl.value && !previewFrameLoading.value) {
    void extractPreviewFrame(previewVideoUrl.value)
  }
  showSubtitleSettings.value = true
}

function closeSubtitleSettings() {
  showSubtitleSettings.value = false
}

async function openClipTemplateLibrary() {
  if (subtitleSettingsEnabled.value) return
  clipTemplateCreatorOpen.value = false
  showClipTemplateLibrary.value = true
  await loadVideoEditTemplates()
}

function closeClipTemplateLibrary() {
  showClipTemplateLibrary.value = false
  clipTemplateCreatorOpen.value = false
  showTemplateBgmLibrary.value = false
}

function resetClipTemplateDraft() {
  clipTemplateDraft.id = `custom_${Date.now()}`
  clipTemplateDraft.name = '未命名模板'
  clipTemplateDraft.coverAdded = false
  clipTemplateDraft.coverUrl = ''
  clipTemplateDraft.titleMode = 'none'
  clipTemplateDraft.titleSubtitleText = previewSubtitleText.value
  clipTemplateDraft.titleAlign = 'top-left'
  clipTemplateDraft.titleFont = 'default'
  clipTemplateDraft.titleSize = 24
  clipTemplateDraft.titleOffsetX = 0
  clipTemplateDraft.titleOffsetY = 0
  clipTemplateDraft.titleSubtitleSize = 13
  clipTemplateDraft.badgeFont = 'default'
  clipTemplateDraft.badgeText = previewTagText.value
  clipTemplateDraft.badgeSize = 12
  clipTemplateDraft.badgeOffsetX = 0
  clipTemplateDraft.badgeOffsetY = 0
  clipTemplateDraft.bgmVolume = Math.round(Number(bgmVolumeSlider.value) || 30)
  clipTemplateDraft.subtitleMode = 'clean'
  clipTemplateDraft.subtitleAlign = 'center'
  clipTemplateDraft.subtitleFont = 'default'
  clipTemplateDraft.subtitleSize = 15
  clipTemplateDraft.subtitleOffsetX = 0
  clipTemplateDraft.subtitleOffsetY = 0
  clipTemplateDraft.subtitleDoubleLine = false
}

function openClipTemplateCreator() {
  resetClipTemplateDraft()
  clipTemplateCreatorOpen.value = true
}

function stringFromConfig(config: Record<string, unknown>, key: string, fallback: string) {
  const value = config[key]
  return typeof value === 'string' ? value : fallback
}

function numberFromConfig(config: Record<string, unknown>, key: string, fallback: number) {
  const value = Number(config[key])
  return Number.isFinite(value) ? value : fallback
}

function booleanFromConfig(config: Record<string, unknown>, key: string, fallback: boolean) {
  const value = config[key]
  return typeof value === 'boolean' ? value : fallback
}

function editClipTemplate(templateValue: string) {
  const item = userClipTemplateCards.value.find((card) => card.value === templateValue)
  if (!item) return

  const config = item.editorConfig || {}
  clipTemplateDraft.id = String(item.templateId)
  clipTemplateDraft.name = item.label || '未命名模板'
  clipTemplateDraft.coverAdded = Boolean(item.thumbnailUrl)
  clipTemplateDraft.coverUrl = item.thumbnailUrl || ''
  clipTemplateDraft.titleMode = stringFromConfig(config, 'titleMode', item.renderConfig.title?.enabled ? String(item.renderConfig.title.mode || 'single') : 'none')
  clipTemplateDraft.titleSubtitleText = stringFromConfig(config, 'titleSubtitleText', String(item.renderConfig.title?.subtitle || '这里是副标题'))
  clipTemplateDraft.titleAlign = stringFromConfig(config, 'titleAlign', 'top-left')
  clipTemplateDraft.titleFont = stringFromConfig(config, 'titleFont', 'default')
  clipTemplateDraft.titleSize = numberFromConfig(config, 'titleSize', Math.max(18, Math.round(Number(item.renderConfig.title?.fontSize || 46) / 1.8)))
  clipTemplateDraft.titleOffsetX = numberFromConfig(config, 'titleOffsetX', Number(item.renderConfig.title?.x || 0))
  clipTemplateDraft.titleOffsetY = numberFromConfig(config, 'titleOffsetY', 0)
  clipTemplateDraft.titleSubtitleSize = numberFromConfig(config, 'titleSubtitleSize', Math.max(10, Math.round(Number(item.renderConfig.title?.subtitleFontSize || 30) / 1.8)))
  clipTemplateDraft.badgeFont = stringFromConfig(config, 'badgeFont', 'default')
  clipTemplateDraft.badgeText = stringFromConfig(config, 'badgeText', String(item.renderConfig.title?.badge || '标签'))
  clipTemplateDraft.badgeSize = numberFromConfig(config, 'badgeSize', Math.max(10, Math.round(Number(item.renderConfig.title?.badgeFontSize || 22) / 1.7)))
  clipTemplateDraft.badgeOffsetX = numberFromConfig(config, 'badgeOffsetX', Number(item.renderConfig.title?.badgeX || 0))
  clipTemplateDraft.badgeOffsetY = numberFromConfig(config, 'badgeOffsetY', Number(item.renderConfig.title?.badgeY || 0))
  clipTemplateDraft.bgmVolume = numberFromConfig(config, 'bgmVolume', Math.round(Number(item.renderConfig.audio?.bgmVolume ?? 0.2) * 100))
  clipTemplateDraft.subtitleMode = stringFromConfig(config, 'subtitleMode', 'clean')
  clipTemplateDraft.subtitleAlign = stringFromConfig(config, 'subtitleAlign', item.subtitleAlign)
  clipTemplateDraft.subtitleFont = stringFromConfig(config, 'subtitleFont', 'default')
  clipTemplateDraft.subtitleSize = numberFromConfig(config, 'subtitleSize', Math.max(12, Math.round(Number(item.renderConfig.subtitle?.fontSize || 42) / 1.9)))
  clipTemplateDraft.subtitleOffsetX = numberFromConfig(config, 'subtitleOffsetX', Number(item.renderConfig.subtitle?.x || 0))
  clipTemplateDraft.subtitleOffsetY = numberFromConfig(config, 'subtitleOffsetY', 0)
  clipTemplateDraft.subtitleDoubleLine = booleanFromConfig(config, 'subtitleDoubleLine', Boolean(item.renderConfig.subtitle?.doubleLine))
  clipTemplateCreatorOpen.value = true
}

function openClipTemplateCoverUpload() {
  if (clipTemplateCoverUploading.value) return
  clipTemplateCoverUploadInput.value?.click()
}

async function handleClipTemplateCoverFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!file.type.startsWith('image/')) {
    window.alert('请上传图片作为模板封面')
    return
  }

  clipTemplateCoverUploading.value = true
  try {
    clipTemplateDraft.coverUrl = await uploadFileToObjectStorage(file, 'clip_template_cover', 'image')
    clipTemplateDraft.coverAdded = true
  } catch (error) {
    console.error('Failed to upload clip template cover', error)
    window.alert(error instanceof Error ? error.message : '模板封面上传失败')
  } finally {
    clipTemplateCoverUploading.value = false
  }
}

function buildClipTemplateEditorConfig() {
  return {
    ...clipTemplateDraft,
  }
}

function mapVideoEditTemplateToCard(template: VideoEditTemplateRead, index: number) {
  const renderConfig = template.render_config
  const subtitleMode = renderConfig.subtitle?.mode === 'highlight' || renderConfig.subtitle?.mode === 'brand'
    ? 'brand'
    : renderConfig.subtitle?.mode === 'double' || renderConfig.subtitle?.mode === 'digital'
      ? 'digital'
      : 'default'
  return {
    templateId: template.id,
    value: `user_${template.id}`,
    code: `U${index + 1}`,
    label: template.name,
    description: template.description || '',
    titleTemplate: renderConfig.title?.enabled ? 'headline_tag' : 'none',
    subtitleMode: subtitleMode as 'default' | 'brand' | 'digital',
    subtitleFontSize: Math.max(28, Math.min(64, Math.round(Number(renderConfig.subtitle?.fontSize || 42)))),
    subtitleOffsetY: Math.max(24, Math.min(180, 64)),
    subtitleAlign: renderConfig.subtitle?.align === 'left' || renderConfig.subtitle?.align === 'right'
      ? renderConfig.subtitle.align
      : 'center' as const,
    renderConfig,
    thumbnailUrl: template.thumbnail_url || null,
    editorConfig: template.editor_config || {},
  }
}

async function loadVideoEditTemplates(options: { silent?: boolean } = {}) {
  if (clipTemplatesLoading.value) return
  clipTemplatesLoading.value = true
  try {
    const sceneCode = purposeSceneCodeMap[props.purposeScene]
    const data = await request<VideoEditTemplateListResponse>(`/api/v1/video-edit-templates?template_type=clip&scene_code=${encodeURIComponent(sceneCode)}`)
    userClipTemplateCards.value = (data.items || [])
      .filter((item) => item.source_type !== 'official')
      .map(mapVideoEditTemplateToCard)
  } catch (error) {
    console.error('Failed to load video edit templates', error)
    if (!options.silent) {
      window.alert(error instanceof Error ? error.message : '模板加载失败')
    }
  } finally {
    clipTemplatesLoading.value = false
  }
}

async function saveClipTemplateDraft() {
  if (savingClipTemplate.value) return
  const label = clipTemplateDraft.name.trim() || '未命名模板'
  if (!clipTemplateDraft.coverUrl) {
    window.alert('请先上传真实图片作为模板封面')
    return
  }
  const renderConfig = buildClipTemplateDraftRenderConfig()
  savingClipTemplate.value = true
  try {
    const editingTemplateId = /^\d+$/.test(clipTemplateDraft.id) ? Number(clipTemplateDraft.id) : null
    const saved = await request<VideoEditTemplateRead>(
      editingTemplateId ? `/api/v1/video-edit-templates/${editingTemplateId}` : '/api/v1/video-edit-templates',
      {
        method: editingTemplateId ? 'PATCH' : 'POST',
        body: {
          name: label,
          description: '',
          template_type: 'clip',
          scene_code: purposeSceneCodeMap[props.purposeScene],
          render_config: renderConfig,
          editor_config: buildClipTemplateEditorConfig(),
          thumbnail_url: clipTemplateDraft.coverUrl || null,
        },
      },
    )
    await loadVideoEditTemplates()
    const selectedCard = userClipTemplateCards.value.find((item) => item.templateId === saved.id)
    customClipRenderConfig.value = saved.render_config
    selectedClipTemplate.value = selectedCard?.value || `user_${saved.id}`
    subtitleSettingsEnabled.value = false
    clipTemplateCreatorOpen.value = false
  } catch (error) {
    console.error('Failed to save video edit template', error)
    window.alert(error instanceof Error ? error.message : '模板保存失败')
  } finally {
    savingClipTemplate.value = false
  }
}

function openTemplateBackgroundUpload() {
  if (backgroundMode.value === 'original') {
    backgroundMode.value = 'image_fill'
  }
  openBackgroundUpload()
}

function applyClipTemplateRuntimeDefaults(options: {
  subtitleEnabled: boolean
  tagEnabled: boolean
  subtitle?: string | null
  badge?: string | null
}) {
  if (options.subtitleEnabled) {
    const nextSubtitle = String(options.subtitle || '').trim()
    overlaySubtitle.value = nextSubtitle || overlaySubtitle.value.trim()
  } else {
    overlaySubtitle.value = ''
  }

  if (options.tagEnabled) {
    const nextTag = String(options.badge || '').trim()
    overlayTag.value = nextTag || overlayTag.value.trim()
  } else {
    overlayTag.value = ''
  }
}

function applyClipTemplate(templateValue: string) {
  const option = clipTemplateOptions.find((item) => item.value === templateValue)
  if (!option) {
    const userOption = userClipTemplateCards.value.find((item) => item.value === templateValue)
    if (userOption) {
      applyClipTemplateRuntimeDefaults({
        subtitleEnabled: renderTitleModeSupportsSubtitle(userOption.renderConfig.title?.mode),
        tagEnabled: userOption.renderConfig.title?.mode === 'badge',
        subtitle: String(userOption.renderConfig.title?.subtitle || ''),
        badge: String(userOption.renderConfig.title?.badge || ''),
      })
      customClipRenderConfig.value = userOption.renderConfig
      selectedClipTemplate.value = userOption.value
      subtitleSettingsEnabled.value = false
      closeClipTemplateLibrary()
    }
    return
  }
  const titleSupport = titleTemplateSupportMeta(String(option.titleTemplate || 'none'))
  applyClipTemplateRuntimeDefaults({
    subtitleEnabled: titleSupport.supportsSubtitle,
    tagEnabled: titleSupport.supportsTag,
  })
  customClipRenderConfig.value = null
  selectedClipTemplate.value = option.value
  titleTemplate.value = option.titleTemplate as typeof titleTemplate.value
  subtitleMode.value = option.subtitleMode as typeof subtitleMode.value
  subtitleFontSizeSlider.value = String(option.subtitleFontSize)
  subtitleOffsetYSlider.value = String(option.subtitleOffsetY)
  subtitleAlign.value = option.subtitleAlign as typeof subtitleAlign.value
  closeClipTemplateLibrary()
}

function resolveClipTemplate(value: unknown) {
  const raw = String(value || '').trim()
  if (clipTemplateOptions.some((item) => item.value === raw)) {
    return raw
  }
  return raw.startsWith('user_') ? raw : 'manual_subtitle'
}

async function runClipRender() {
  if (clippingVideo.value) {
    return
  }
  if (!draftId.value) {
    window.alert('请先将当前内容保存为创作草稿后再进行剪辑。')
    return
  }
  if (!generatedVideoUrl.value) {
    window.alert('请先生成数字人成片后再使用剪辑功能。')
    return
  }
  bgmMode.value = bgmAssetUrl.value.trim() ? 'uploaded' : 'none'
  clipTemplate.value = 'talking_head'
  clippingVideo.value = true
  clipRenderStage.value = '准备剪辑参数...'
  const clipAbort = new AbortController()
  const clipTimer = window.setTimeout(() => clipAbort.abort(), 900_000)
  try {
    let timelineSegments = buildVoiceTimelineSegments()
    if (!timelineSegments.length) {
      clipRenderStage.value = '检查口播时间轴...'
      timelineSegments = await syncVoiceTimelineFromGeneratedAudio({ silent: true })
    }
    clipRenderStage.value = '保存草稿...'
    await saveDraftNow()
    clipRenderStage.value = '后端剪辑渲染中...'
    const clipBody: { segments?: SubtitleTimelineSegment[]; render_config: ClipRenderConfig } = {
      render_config: activeClipRenderConfig.value,
    }
    if (timelineSegments.length) {
      clipBody.segments = timelineSegments
    }
    const res = await request<ClipRenderResponse>(`${currentDraftApiBase.value}/${draftId.value}/clip-render`, {
      method: 'POST',
      signal: clipAbort.signal,
      body: clipBody,
    })
    persistedClipParams.value = { ...(res.draft.clip_params || {}) }
    clipRenderStage.value = '加载剪辑预览...'
    await refreshClippedPreview()
    void saveDraftNow()
  } catch (error) {
    if (!(error instanceof ApiError && error.status >= 400 && error.status < 500)) {
      console.error('clip render failed', error)
    }
    const message = error instanceof Error && error.message
      ? error.message
      : '剪辑处理未能完成。请确认文案服务可正常访问、素材地址可用、应用服务器已安装 FFmpeg。'
    window.alert(message)
  } finally {
    window.clearTimeout(clipTimer)
    clippingVideo.value = false
    clipRenderStage.value = ''
  }
}

async function parseJsonSafely(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    return null
  }
  return response.json()
}

function formatDuration(totalSeconds: number) {
  const safeSeconds = Math.max(0, Math.round(totalSeconds))
  const minutes = Math.floor(safeSeconds / 60)
  const seconds = safeSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

async function getAudioDurationSeconds(url: string) {
  return await new Promise<number>((resolve, reject) => {
    const audio = new Audio()
    const cleanup = () => {
      audio.removeEventListener('loadedmetadata', onLoaded)
      audio.removeEventListener('error', onError)
    }
    const onLoaded = () => {
      cleanup()
      resolve(Number.isFinite(audio.duration) ? audio.duration : 0)
    }
    const onError = () => {
      cleanup()
      reject(new Error('音频时长读取失败'))
    }
    audio.preload = 'metadata'
    audio.addEventListener('loadedmetadata', onLoaded)
    audio.addEventListener('error', onError)
    audio.src = url
  })
}

function normalizeTimelineSegments(raw: unknown): SubtitleTimelineSegment[] {
  if (!Array.isArray(raw)) return []
  return raw
    .map((item) => ({
      start: Number((item as Record<string, unknown>)?.start ?? 0),
      end: Number((item as Record<string, unknown>)?.end ?? 0),
      text: String((item as Record<string, unknown>)?.text || '').trim(),
    }))
    .filter((item) => Number.isFinite(item.start) && Number.isFinite(item.end) && item.end > item.start)
    .map((item) => ({
      start: Number(item.start.toFixed(3)),
      end: Number(item.end.toFixed(3)),
      text: item.text,
    }))
}

async function ensureGeneratedAudioDuration() {
  if (generatedAudioDurationSeconds.value > 0) {
    return generatedAudioDurationSeconds.value
  }
  for (const raw of [generatedAudioUrl.value, generatedAudioLocalUrl.value, generatedAudioSourceUrl.value]) {
    const url = String(raw || '').trim()
    if (!url) continue
    try {
      const duration = await getAudioDurationSeconds(url)
      if (duration > 0) {
        generatedAudioDurationSeconds.value = duration
        return duration
      }
    } catch (error) {
      console.warn('Failed to read generated audio duration', error)
    }
  }
  return 0
}

function buildRewriteInstruction(extra?: string) {
  const parts = [rewriteTemplate.value, rewriteTone.value]
  if (extra) parts.push(extra)
  return parts.filter(Boolean).join('，')
}

function splitTalkScriptLines(text: string) {
  const byLine = text
    .split(/\r?\n+/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (byLine.length > 1) return byLine
  const chunks = text.match(/[^。！？!?；;\n]+[。！？!?；;]?/g) || []
  return chunks.map((item) => item.trim()).filter(Boolean)
}

function mapScriptToTimelineSegments(script: string, segments: SubtitleTimelineSegment[]) {
  const normalized = normalizeTimelineSegments(segments)
  if (!normalized.length) return []

  const text = script.trim()
  if (!text) {
    return normalized.map((item) => ({
      ...item,
      text: item.text.trim() || '...',
    }))
  }

  const weights = normalized.map((item) => Math.max(0.001, item.end - item.start))
  const totalWeight = weights.reduce((sum, value) => sum + value, 0)
  const totalChars = text.length
  let position = 0

  return normalized.map((item, index) => {
    let chunk = ''
    if (index === normalized.length - 1) {
      chunk = text.slice(position)
    } else {
      const share = Math.max(
        0,
        Math.min(
          Math.round(totalChars * (weights[index] / (totalWeight || 1))),
          totalChars - position,
        ),
      )
      chunk = text.slice(position, position + share)
      position += share
    }
    return {
      ...item,
      text: chunk.trim() || item.text.trim() || '...',
    }
  })
}

function buildFallbackTimelineSegments(script: string, duration: number) {
  const text = script.trim()
  const safeDuration = Math.max(0, Number(duration || 0))
  const lines = splitTalkScriptLines(text)
  if (!lines.length || safeDuration <= 0) return []

  const weights = lines.map((line) => Math.max(1, line.length))
  const totalWeight = weights.reduce((sum, value) => sum + value, 0)
  let current = 0

  return lines.map((line, index) => {
    const segmentDuration = totalWeight ? safeDuration * (weights[index] / totalWeight) : safeDuration / lines.length
    const end = index === lines.length - 1 ? safeDuration : Math.min(safeDuration, current + segmentDuration)
    const segment = {
      start: Number(current.toFixed(3)),
      end: Number(end.toFixed(3)),
      text: line,
    }
    current = end
    return segment
  })
}

function buildVoiceTimelineSegments() {
  const script = rewrittenCopy.value.trim() || sourceCopy.value.trim()
  const normalized = normalizeTimelineSegments(voiceTimelineSegments.value)
  if (normalized.length) {
    return mapScriptToTimelineSegments(script, normalized)
  }
  return buildFallbackTimelineSegments(script, generatedAudioDurationSeconds.value)
}

async function syncVoiceTimelineFromGeneratedAudio(options: { silent?: boolean } = {}) {
  const script = rewrittenCopy.value.trim() || sourceCopy.value.trim()
  const media = pickPublicMediaForClipAsr()

  if (media) {
    const transcribeAbort = new AbortController()
    const transcribeTimer = window.setTimeout(() => transcribeAbort.abort(), 25_000)
    try {
      const response = await fetch(`${copywritingApiBaseUrl}/api/v1/copywriting/transcribe-media-url`, {
        method: 'POST',
        headers: buildHeaders(),
        body: JSON.stringify({ media_url: media }),
        signal: transcribeAbort.signal,
      })
      const data = (await parseJsonSafely(response)) as { segments?: unknown } | null
      const normalized = normalizeTimelineSegments(data?.segments)
      if (response.ok && normalized.length) {
        const mapped = mapScriptToTimelineSegments(script, normalized)
        voiceTimelineSegments.value = mapped
        generatedAudioDurationSeconds.value = Math.max(
          generatedAudioDurationSeconds.value,
          Number(mapped[mapped.length - 1]?.end || 0),
        )
        return mapped
      }
    } catch (error) {
      if (!options.silent) {
        console.warn('Transcribe media request failed, fallback to duration split', error)
      }
    } finally {
      window.clearTimeout(transcribeTimer)
    }
  }

  const duration = await ensureGeneratedAudioDuration()
  const fallback = buildFallbackTimelineSegments(script, duration)
  voiceTimelineSegments.value = fallback
  if (fallback.length) {
    generatedAudioDurationSeconds.value = Math.max(
      generatedAudioDurationSeconds.value,
      Number(fallback[fallback.length - 1]?.end || 0),
    )
  }
  return fallback
}

function resolveSubtitleAlign(value: unknown): (typeof subtitleAlignOptions)[number]['value'] {
  return value === 'center' || value === 'right' ? value : 'left'
}

function buildDraftPayload(sceneOverride: AvatarPurposeScene = videoPurposeScene.value) {
  const timelineSegments = buildVoiceTimelineSegments()
  const salesScene: SalesScenePersistedState = {
    product_keyword: productKeyword.value.trim() || null,
    selected_product_id: selectedProductId.value || null,
    selected_product_profile: selectedProductProfile.value || null,
    product_assets: productAssets.value,
    selected_white_image_id: selectedWhiteImageId.value || null,
    selected_wear_image_id: selectedWearImageId.value || null,
    scene_image_url: salesSceneImageUrl.value || null,
    image_count: salesImageCount.value,
    aspect_ratio: salesAspectRatio.value,
    extra_requirements: salesExtraRequirements.value.trim() || null,
    fusion_task_id: fusionTaskId.value || null,
    fusion_task_status: fusionTaskStatus.value || null,
    fusion_images: fusionImages.value,
    selected_fusion_image_url: selectedFusionImageUrl.value || null,
    selected_gallery_image_urls: selectedGalleryImageUrls.value,
    collage_image_url: productCollageImageUrl.value || null,
  }
  return {
    title: resolvedClipVideoTitle.value,
    source_url: sourceUrl.value.trim() || null,
    platform: detectedPlatform.value || null,
    content_id: extractResult.value?.parsed_link.content_id || null,
    content_info: {
      ...(extractResult.value?.content_info ?? {}),
      purpose_scene: sceneOverride,
      product_keyword: productKeyword.value.trim() || null,
      selected_product_id: selectedProductId.value || null,
    },
    transcript: extractResult.value?.transcript ?? {},
    extracted_copy: sourceCopy.value.trim() || null,
    rewrite_instruction: rewriteResult.value?.instruction || null,
    rewritten_copy: rewrittenCopy.value.trim() || null,
    voice_params: {
      mode: voiceMode.value,
      voice_asset_id: selectedVoiceAssetId.value ? Number(selectedVoiceAssetId.value) : null,
      voice_id: selectedVoiceId.value || null,
      profile: voiceProfile.value,
      style: voiceStyle.value,
      speed: voiceSpeed.value,
      similarity: voiceSimilarity.value,
      clone_audio_url: cloneAudioUrl.value || null,
      clone_voice_prefix: cloneVoicePrefix.value || null,
      audio_url: generatedAudioUrl.value || null,
      local_audio_url: generatedAudioLocalUrl.value || null,
      source_audio_url: generatedAudioSourceUrl.value || null,
      record_id: generatedVoiceRecordId.value,
      duration_seconds: generatedAudioDurationSeconds.value || null,
      timeline_segments: timelineSegments,
    },
    digital_human_params: {
      human_type: humanType.value,
      template: digitalTemplate.value,
      scene: digitalScene.value,
      video_purpose: sceneOverride,
      image_url: digitalHumanImageUrl.value || null,
      fusion_image_url: selectedFusionImageUrl.value || null,
      video_url: digitalHumanVideoUrl.value || null,
      generated_video_url: generatedVideoUrl.value || null,
      generated_video_source_url: generatedVideoSourceUrl.value || null,
      task_id: digitalHumanTaskId.value || null,
      task_status: digitalHumanTaskStatus.value || null,
      [currentDraftSceneStateKey.value]: salesScene,
    },
    clip_params: {
      ...persistedClipParams.value,
      render_config: activeClipRenderConfig.value,
      selected_template_code: subtitleSettingsEnabled.value ? 'subtitle_settings' : selectedClipTemplate.value,
      template_runtime_params: {
        selected_template_code: subtitleSettingsEnabled.value ? 'subtitle_settings' : selectedClipTemplate.value,
        subtitle_settings_enabled: subtitleSettingsEnabled.value,
        render_config: activeClipRenderConfig.value,
        subtitle_mode: subtitleMode.value,
        title_template: titleTemplate.value,
        subtitle_font_size: subtitleFontSize.value,
        subtitle_offset_y: subtitleOffsetY.value,
        subtitle_align: subtitleAlign.value,
      },
      subtitle_settings_enabled: subtitleSettingsEnabled.value,
      subtitle_mode: subtitleMode.value,
      subtitle_font_size: subtitleFontSize.value,
      subtitle_offset_y: subtitleOffsetY.value,
      subtitle_align: subtitleAlign.value,
      background_mode: effectiveBackgroundMode.value,
      background_asset_id: backgroundAssetId.value,
      background_asset_name: backgroundAssetName.value || null,
      background_asset_url: backgroundAssetUrl.value || null,
      template_mode: clipTemplate.value,
      title_template: titleTemplate.value,
      overlay_title: resolvedClipVideoTitle.value || null,
      overlay_subtitle: selectedTitleTemplateSupportsSubtitle.value ? (overlaySubtitle.value || null) : null,
      overlay_tag: selectedTitleTemplateSupportsTag.value ? (overlayTag.value || null) : null,
      bgm_mode: bgmAssetUrl.value.trim() ? 'uploaded' : 'none',
      bgm_asset_url: bgmAssetUrl.value || null,
      voice_volume: voiceVolume.value,
      bgm_volume: bgmVolume.value,
    },
    product_keyword: productKeyword.value.trim() || null,
    selected_product_id: selectedProductId.value || null,
    selected_product_profile: selectedProductProfile.value || {},
    product_assets: productAssets.value,
    selected_white_image_id: selectedWhiteImageId.value || null,
    selected_wear_image_id: selectedWearImageId.value || null,
    scene_image_url: salesSceneImageUrl.value || null,
    image_count: salesImageCount.value,
    aspect_ratio: salesAspectRatio.value,
    extra_requirements: salesExtraRequirements.value.trim() || null,
    fusion_task_id: fusionTaskId.value || null,
    fusion_task_status: fusionTaskStatus.value || null,
    fusion_images: fusionImages.value,
    selected_fusion_image_url: selectedFusionImageUrl.value || null,
    status: generatedVideoUrl.value.trim()
      ? 'video_generated'
      : selectedFusionImageUrl.value.trim() || fusionImages.value.length
        ? 'fusion_generated'
        : rewrittenCopy.value.trim()
          ? 'rewritten'
          : sourceCopy.value.trim()
            ? 'extracted'
            : 'draft',
  }
}

function hasPersistableContent() {
  return Boolean(
    sourceUrl.value.trim()
    || sourceCopy.value.trim()
    || rewrittenCopy.value.trim()
    || digitalHumanImageUrl.value.trim()
    || selectedProductId.value
    || selectedFusionImageUrl.value.trim()
    || draftId.value,
  )
}

async function syncDraftRoute(id: string) {
  if (!id || route.query.draftId === id) return
  await router.replace({
    query: {
      ...route.query,
      draftId: id,
    },
  })
}

async function saveDraftNow(sceneOverride: AvatarPurposeScene = videoPurposeScene.value) {
  if (hydratingDraft.value || !hasPersistableContent()) return

  draftSaving.value = true
  try {
    const payload = buildDraftPayload(sceneOverride)
    let saved: AvatarSalesDraftRead
    if (draftId.value) {
      saved = await request<AvatarSalesDraftRead>(`${currentDraftApiBase.value}/${draftId.value}`, {
        method: 'PATCH',
        body: payload,
      })
    } else {
      saved = await request<AvatarSalesDraftRead>(currentDraftApiBase.value, {
        method: 'POST',
        body: payload,
      })
    }
    draftId.value = saved.draft_id
    await syncDraftRoute(saved.draft_id)
  } catch (error) {
    console.error('Failed to persist creation draft', error)
  } finally {
    draftSaving.value = false
  }
}

function scheduleDraftSave() {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  draftSaveTimer = setTimeout(() => {
    void saveDraftNow()
  }, 500)
}

async function handleSceneSwitch(targetScene: AvatarPurposeScene, sourceScene: AvatarPurposeScene) {
  if (!targetScene || targetScene === sourceScene || switchingScene.value) return
  const targetPath = purposeSceneRouteMap[targetScene]
  if (!targetPath) return

  switchingScene.value = true
  try {
    await router.push({
      path: targetPath,
      query: buildDraftlessQuery(route.query),
    })
  } catch (error) {
    videoPurposeScene.value = sourceScene
    console.error('Failed to switch creation scene', error)
  } finally {
    switchingScene.value = false
  }
}

async function applyDraftToView(draft: AvatarSalesDraftRead) {
  hydratingDraft.value = true
  try {
    draftId.value = draft.draft_id
    clipVideoTitle.value = String(draft.title || '').trim()
    sourceUrl.value = draft.source_url || ''
    sourceCopy.value = draft.extracted_copy || ''
    rewrittenCopy.value = draft.rewritten_copy || ''

    if (draft.platform || draft.content_id || Object.keys(draft.content_info || {}).length > 0) {
      extractResult.value = {
        url: draft.source_url || '',
        parsed_link: {
          platform: String(draft.platform || ''),
          content_id: String(draft.content_id || ''),
          original_url: draft.source_url || '',
          is_short_link: false,
        },
        content_info: draft.content_info as ExtractCopyResponse['content_info'],
        transcript: draft.transcript as ExtractCopyResponse['transcript'],
        extracted_copy: draft.extracted_copy || '',
        llm_config_name: null,
        model_name: null,
      }
    } else {
      extractResult.value = null
    }

    if (draft.rewritten_copy) {
      rewriteResult.value = {
        source_text: draft.extracted_copy || '',
        rewritten_text: draft.rewritten_copy,
        instruction: draft.rewrite_instruction || null,
        llm_config_name: null,
        model_name: null,
      }
    } else {
      rewriteResult.value = null
    }

    const voiceParams = draft.voice_params || {}
    voiceMode.value = voiceParams.mode === 'clone' ? 'clone' : 'system'
    showCloneCreator.value = false
    selectedVoiceAssetId.value = voiceParams.voice_asset_id ? String(voiceParams.voice_asset_id) : ''
    selectedVoiceId.value = String(voiceParams.voice_id || '')
    voiceProfile.value = String(voiceParams.profile || '新闻男声')
    voiceStyle.value = String(voiceParams.style || '自然陈述')
    voiceSpeedSlider.value = String(
      Math.max(0, Math.min(100, Math.round(((Number(voiceParams.speed ?? 1) - 0.5) / 1.5) * 100))),
    )
    voiceSimilaritySlider.value = String(Math.round(Number(voiceParams.similarity ?? 0.3) * 100))
    cloneAudioUrl.value = String(voiceParams.clone_audio_url || '')
    cloneVoicePrefix.value = String(voiceParams.clone_voice_prefix || 'myvoice')
    generatedAudioUrl.value = String(voiceParams.audio_url || '')
    generatedAudioLocalUrl.value = String(voiceParams.local_audio_url || '')
    generatedAudioSourceUrl.value = String(voiceParams.source_audio_url || '')
    generatedVoiceRecordId.value = voiceParams.record_id ? Number(voiceParams.record_id) : null
    voiceTimelineSegments.value = normalizeTimelineSegments(voiceParams.timeline_segments)
    generatedAudioDurationSeconds.value = Math.max(
      Number(voiceParams.duration_seconds || 0),
      Number(voiceTimelineSegments.value[voiceTimelineSegments.value.length - 1]?.end || 0),
    )

    const digitalParams = draft.digital_human_params || {}
    const persistedSalesScene = (
      (digitalParams[currentDraftSceneStateKey.value] as SalesScenePersistedState | undefined)
      || (digitalParams.sales_scene as SalesScenePersistedState | undefined)
      || (digitalParams.product_scene as SalesScenePersistedState | undefined)
      || {}
    ) as SalesScenePersistedState
    const salesScene = {
      ...persistedSalesScene,
      product_keyword: draft.product_keyword ?? persistedSalesScene.product_keyword ?? null,
      selected_product_id: draft.selected_product_id ?? persistedSalesScene.selected_product_id ?? null,
      selected_product_profile: Object.keys(draft.selected_product_profile || {}).length
        ? draft.selected_product_profile as BrandProfile
        : (persistedSalesScene.selected_product_profile ?? null),
      product_assets: Array.isArray(draft.product_assets) && draft.product_assets.length
        ? draft.product_assets as VisualAssetItem[]
        : (persistedSalesScene.product_assets ?? []),
      selected_white_image_id: draft.selected_white_image_id ?? persistedSalesScene.selected_white_image_id ?? null,
      selected_wear_image_id: draft.selected_wear_image_id ?? persistedSalesScene.selected_wear_image_id ?? null,
      scene_image_url: draft.scene_image_url ?? persistedSalesScene.scene_image_url ?? null,
      image_count: draft.image_count ?? persistedSalesScene.image_count ?? 4,
      aspect_ratio: draft.aspect_ratio ?? persistedSalesScene.aspect_ratio ?? '3:4',
      extra_requirements: draft.extra_requirements ?? persistedSalesScene.extra_requirements ?? null,
      fusion_task_id: draft.fusion_task_id ?? persistedSalesScene.fusion_task_id ?? null,
      fusion_task_status: draft.fusion_task_status ?? persistedSalesScene.fusion_task_status ?? null,
      fusion_images: Array.isArray(draft.fusion_images) && draft.fusion_images.length
        ? draft.fusion_images as GalleryImageItem[]
        : (persistedSalesScene.fusion_images ?? []),
      selected_fusion_image_url: draft.selected_fusion_image_url ?? persistedSalesScene.selected_fusion_image_url ?? null,
    } as SalesScenePersistedState
    humanType.value = digitalParams.human_type === 'video' ? 'video' : 'image'
    digitalTemplate.value = String(digitalParams.template || '品牌讲解型')
    digitalScene.value = String(digitalParams.scene || '极简直播间')
    videoPurposeScene.value = props.purposeScene
    digitalHumanImageUrl.value = String(digitalParams.image_url || '')
    digitalHumanVideoUrl.value = String(digitalParams.video_url || '')
    digitalHumanImageWidth.value = 0
    digitalHumanImageHeight.value = 0
    digitalHumanVideoWidth.value = 0
    digitalHumanVideoHeight.value = 0
    generatedVideoUrl.value = String(digitalParams.generated_video_url || '')
    generatedVideoSourceUrl.value = String(digitalParams.generated_video_source_url || digitalParams.generated_video_url || '')
    digitalHumanTaskId.value = String(digitalParams.task_id || '')
    digitalHumanTaskStatus.value = String(digitalParams.task_status || '')
    productKeyword.value = String(salesScene.product_keyword || draft.content_info?.product_keyword || '')
    selectedProductId.value = String(salesScene.selected_product_id || draft.content_info?.selected_product_id || '')
    selectedProductProfile.value = (salesScene.selected_product_profile || null) as BrandProfile | null
    productAssets.value = Array.isArray(salesScene.product_assets) ? salesScene.product_assets : []
    selectedWhiteImageId.value = String(salesScene.selected_white_image_id || '')
    selectedWearImageId.value = String(salesScene.selected_wear_image_id || '')
    salesSceneImageUrl.value = String(salesScene.scene_image_url || '')
    salesImageCount.value = Math.max(4, Number(salesScene.image_count || 4))
    salesAspectRatio.value = String(salesScene.aspect_ratio || '3:4')
    salesExtraRequirements.value = String(salesScene.extra_requirements || '')
    instructionGenerationRunId += 1
    instructionGenerating.value = false
    instructionGenerationError.value = ''
    fusionTaskId.value = String(salesScene.fusion_task_id || '')
    fusionTaskStatus.value = String(salesScene.fusion_task_status || '')
    fusionImages.value = normalizeFusionImages(Array.isArray(salesScene.fusion_images) ? salesScene.fusion_images : [])
    selectedGalleryImageUrls.value = Array.isArray(salesScene.selected_gallery_image_urls) ? salesScene.selected_gallery_image_urls : []
    productCollageImageUrl.value = String(salesScene.collage_image_url || '')
    selectedFusionImageUrl.value = String(
      salesScene.selected_fusion_image_url
      || digitalParams.fusion_image_url
      || fusionImages.value[0]?.url
      || '',
    )
    if (selectedProductId.value && (!selectedProductProfile.value || !productAssets.value.length)) {
      try {
        await selectProduct(selectedProductId.value)
      } catch (error) {
        console.error('Failed to restore sales product context', error)
      }
    }

    const clipParams = draft.clip_params || {}
    persistedClipParams.value = { ...clipParams }
    subtitleSettingsEnabled.value = clipParams.subtitle_settings_enabled !== false
    selectedClipTemplate.value = resolveClipTemplate(clipParams.selected_template_code)
    customClipRenderConfig.value = selectedClipTemplate.value.startsWith('user_') && clipParams.render_config
      ? cloneRenderConfig(clipParams.render_config as ClipRenderConfig)
      : null
    subtitleMode.value = resolveSubtitleMode(clipParams.subtitle_mode)
    subtitleFontSizeSlider.value = String(Math.round(Number(clipParams.subtitle_font_size || 42)))
    subtitleOffsetYSlider.value = String(Math.round(Number(clipParams.subtitle_offset_y || 64)))
    subtitleAlign.value = resolveSubtitleAlign(clipParams.subtitle_align)
    backgroundMode.value = String(clipParams.background_mode || 'original') as typeof backgroundMode.value
    backgroundAssetId.value = Number(clipParams.background_asset_id || 0) || null
    backgroundAssetName.value = String(clipParams.background_asset_name || '')
    backgroundAssetUrl.value = String(clipParams.background_asset_url || '')
    clipTemplate.value = 'talking_head'
    titleTemplate.value = String(clipParams.title_template || 'none') as typeof titleTemplate.value
    overlaySubtitle.value = String(clipParams.overlay_subtitle || '')
    overlayTag.value = String(clipParams.overlay_tag || '')
    bgmMode.value = String(clipParams.bgm_mode || 'none') as typeof bgmMode.value
    bgmAssetUrl.value = String(clipParams.bgm_asset_url || '')
    voiceVolumeSlider.value = String(Math.round(Number(clipParams.voice_volume ?? 1) * 50))
    bgmVolumeSlider.value = String(Math.round(Number(clipParams.bgm_volume ?? 0.3) * 100))
    void refreshClippedPreview()
  } finally {
    hydratingDraft.value = false
  }
}

async function loadDraft(id: string) {
  draftLoading.value = true
  try {
    const matched = await ensureDraftSceneMatchesCurrentPage(id)
    if (!matched) return
    const draft = await request<AvatarSalesDraftRead>(`${currentDraftApiBase.value}/${id}`)
    await applyDraftToView(draft)
  } catch (error) {
    console.error('Failed to load creation draft', error)
  } finally {
    draftLoading.value = false
  }
}

async function loadDraftLibrary() {
  draftLibraryLoading.value = true
    try {
      const data = await request<AvatarSalesDraftListResponse>(`${currentDraftApiBase.value}?limit=20&offset=0`)
      const currentSceneCode = purposeSceneCodeMap[props.purposeScene]
      draftLibraryItems.value = (data.items || []).map((item) => ({
        draft_id: item.draft_id,
        user_id: item.user_id,
        scene_code: currentSceneCode,
        title: item.title,
        status: item.status,
        current_step_code: null,
      progress: null,
      created_at: item.created_at,
      updated_at: item.updated_at,
    }))
  } catch (error) {
    console.error('Failed to load creation draft library', error)
    draftLibraryItems.value = []
  } finally {
    draftLibraryLoading.value = false
  }
}

function openDraftLibrary() {
  showDraftLibrary.value = true
  void loadDraftLibrary()
}

function closeDraftLibrary() {
  showDraftLibrary.value = false
}

function toggleModeMenu() {
  showModeMenu.value = !showModeMenu.value
}

function selectMode(mode: 'manual' | 'auto' | 'batch') {
  currentMode.value = mode
  showModeMenu.value = false
}

async function handleSelectDraft(id: string, scene?: AvatarPurposeScene) {
  const targetScene = scene || props.purposeScene
  const targetPath = purposeSceneRouteMap[targetScene]
  if (targetPath && route.path !== targetPath) {
    closeDraftLibrary()
    await router.push({
      path: targetPath,
      query: {
        ...route.query,
        draftId: id,
      },
    })
    return
  }
  await loadDraft(id)
  closeDraftLibrary()
}

function handlePublishDraft(id: string) {
  window.postMessage({
    type: 'openNewPlanModal',
    mode: 'avatarOnly',
    draftId: id,
  }, '*')
  closeDraftLibrary()
}

async function handleDeleteDraft(id: string) {
  const confirmed = window.confirm('确定删除这条草稿吗？')
  if (!confirmed) return

  try {
    await request(`${currentDraftApiBase.value}/${id}`, {
      method: 'DELETE',
    })
    if (draftId.value === id) {
      await handleCreateNewContent()
    } else {
      await loadDraftLibrary()
    }
  } catch (error) {
    console.error('Failed to delete creation draft', error)
    window.alert('删除草稿失败')
  }
}

async function handleCreateNewContent() {
  hydratingDraft.value = true
  try {
    draftId.value = ''
    clipVideoTitle.value = ''
    sourceUrl.value = ''
    sourceCopy.value = ''
    rewrittenCopy.value = ''
    extractResult.value = null
    rewriteResult.value = null
    voiceMode.value = 'system'
    showCloneCreator.value = false
    voiceProfile.value = '新闻男声'
    voiceStyle.value = '自然陈述'
    voiceSpeedSlider.value = '33'
    voiceSimilaritySlider.value = '30'
    selectedVoiceAssetId.value = ''
    selectedVoiceId.value = ''
    cloneAudioUrl.value = ''
    cloneVoicePrefix.value = 'myvoice'
    generatedAudioUrl.value = ''
    generatedAudioLocalUrl.value = ''
    generatedAudioSourceUrl.value = ''
    generatedVoiceRecordId.value = null
    generatedAudioDurationSeconds.value = 0
    voiceTimelineSegments.value = []
    humanType.value = 'image'
    digitalTemplate.value = '品牌讲解型'
    digitalScene.value = '极简直播间'
    videoPurposeScene.value = props.purposeScene
    digitalHumanImageUrl.value = ''
    digitalHumanVideoUrl.value = ''
    digitalHumanImageWidth.value = 0
    digitalHumanImageHeight.value = 0
    digitalHumanVideoWidth.value = 0
    digitalHumanVideoHeight.value = 0
    generatedVideoUrl.value = ''
    generatedVideoSourceUrl.value = ''
    previewFrameDataUrl.value = ''
    previewFrameWidth.value = 0
    previewFrameHeight.value = 0
    previewFrameLoading.value = false
    digitalHumanTaskId.value = ''
    digitalHumanTaskStatus.value = ''
    productKeyword.value = ''
    selectedProductId.value = ''
    selectedProductProfile.value = null
    productAssets.value = []
    selectedWhiteImageId.value = ''
    selectedWearImageId.value = ''
    salesSceneImageUrl.value = ''
    salesImageCount.value = 4
    salesAspectRatio.value = '3:4'
    salesExtraRequirements.value = ''
    instructionGenerationRunId += 1
    instructionGenerating.value = false
    instructionGenerationError.value = ''
    fusionTaskId.value = ''
    fusionTaskStatus.value = ''
    fusionImages.value = []
    selectedGalleryImageUrls.value = []
    productCollageImageUrl.value = ''
    selectedFusionImageUrl.value = ''
    fusionPreviewImage.value = null
    showInstructionDialog.value = false
    subtitleSettingsEnabled.value = true
    subtitleMode.value = 'default'
    subtitleFontSizeSlider.value = '42'
    subtitleOffsetYSlider.value = '64'
    subtitleAlign.value = 'center'
    backgroundMode.value = 'original'
    backgroundAssetId.value = null
    backgroundAssetName.value = ''
    backgroundAssetUrl.value = ''
    clipTemplate.value = 'talking_head'
    selectedClipTemplate.value = 'manual_subtitle'
    titleTemplate.value = 'none'
    overlaySubtitle.value = ''
    overlayTag.value = ''
    customClipRenderConfig.value = null
    clipStylePreviewExpanded.value = false
    clipRenderStage.value = ''
    clipTemplateCreatorOpen.value = false
    showTemplateBgmLibrary.value = false
    bgmMode.value = 'none'
    bgmAssetUrl.value = ''
    voiceVolumeSlider.value = '50'
    bgmVolumeSlider.value = '30'
    persistedClipParams.value = {}
    clippedPreviewUrl.value = ''
    if (clipBlobUrl.value) {
      URL.revokeObjectURL(clipBlobUrl.value)
      clipBlobUrl.value = null
    }
    if (route.query.draftId) {
      await router.replace({ query: buildDraftlessQuery(route.query) })
    }
  } finally {
    hydratingDraft.value = false
  }
  await loadDraftLibrary()
  await loadProducts()
  closeDraftLibrary()
}

function selectHumanType(type: 'image' | 'video') {
  humanType.value = 'image'
}

function handleDigitalHumanImageLoad(event: Event) {
  const image = event.target as HTMLImageElement | null
  digitalHumanImageWidth.value = image?.naturalWidth || 0
  digitalHumanImageHeight.value = image?.naturalHeight || 0
}

function handleDigitalHumanVideoMetadata(event: Event) {
  const video = event.target as HTMLVideoElement | null
  digitalHumanVideoWidth.value = video?.videoWidth || 0
  digitalHumanVideoHeight.value = video?.videoHeight || 0
}

async function getImageNaturalSize(url: string) {
  return await new Promise<{ width: number; height: number }>((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve({ width: image.naturalWidth || 0, height: image.naturalHeight || 0 })
    image.onerror = () => reject(new Error('图片尺寸读取失败'))
    image.src = url
  })
}

function mapSizeToOutputSpec(width: number, height: number) {
  if (width > 0 && height > 0) {
    const ratio = width / height
    const orientation = ratio > 1.05 ? 'landscape' : ratio < 0.95 ? 'portrait' : 'square'
    const candidates = salesVideoResolutionCandidates.filter((item) => {
      const candidateRatio = item.width / item.height
      const candidateOrientation = candidateRatio > 1.05 ? 'landscape' : candidateRatio < 0.95 ? 'portrait' : 'square'
      return candidateOrientation === orientation
    })
    const pool = candidates.length ? candidates : salesVideoResolutionCandidates
    const best = pool.reduce((closest, item) => {
      const currentDiff = Math.abs((item.width / item.height) - ratio)
      const bestDiff = Math.abs((closest.width / closest.height) - ratio)
      if (currentDiff !== bestDiff) {
        return currentDiff < bestDiff ? item : closest
      }
      const currentPixels = item.width * item.height
      const bestPixels = closest.width * closest.height
      return currentPixels < bestPixels ? item : closest
    })
    return {
      aspectRatio: best.aspectRatio,
      resolution: best.resolution,
    }
  }

  return {
    aspectRatio: '9:16',
    resolution: '1080x1920 (9:16) (竖屏)',
  }
}

async function resolveDigitalHumanOutputSpec() {
  const preferredImageUrl = (
    isProductIntroScene.value && productCollageImageUrl.value.trim()
      ? productCollageImageUrl.value.trim()
      : selectedFusionImageUrl.value.trim()
  )
  if (preferredImageUrl) {
    try {
      const size = await getImageNaturalSize(preferredImageUrl)
      return mapSizeToOutputSpec(size.width, size.height)
    } catch (error) {
      console.warn('Failed to resolve fusion image size, fallback to current digital human asset', error)
    }
  }
  const width = humanType.value === 'video' ? digitalHumanVideoWidth.value : digitalHumanImageWidth.value
  const height = humanType.value === 'video' ? digitalHumanVideoHeight.value : digitalHumanImageHeight.value
  return mapSizeToOutputSpec(width, height)
}

function openImageUpload() {
  if (imageUploading.value || videoUploading.value) return
  humanType.value = 'image'
  imageUploadInput.value?.click()
}

function openVideoUpload() {
  if (imageUploading.value || videoUploading.value) return
  humanType.value = 'video'
  videoUploadInput.value?.click()
}

function handleGeneratedAudioMetadata(event: Event) {
  const audio = event.target as HTMLAudioElement | null
  const duration = audio && Number.isFinite(audio.duration) ? audio.duration : 0
  generatedAudioDurationSeconds.value = Math.max(
    duration,
    Number(voiceTimelineSegments.value[voiceTimelineSegments.value.length - 1]?.end || 0),
  )
}

async function uploadFileToObjectStorage(file: File, module: string, mediaType: 'image' | 'video' | 'audio') {
  const ticket = await request<UploadTicketRead>('/api/v1/uploads/ticket', {
    method: 'POST',
    body: {
      module,
      media_type: mediaType,
      file_name: file.name,
      content_type: file.type || 'application/octet-stream',
      draft_id: draftId.value || null,
    },
  })

  const response = await fetch(ticket.upload_url, {
    method: ticket.upload_method || 'PUT',
    headers: {
      'Content-Type': file.type || ticket.content_type || 'application/octet-stream',
    },
    body: file,
  })
  if (!response.ok) {
    throw new Error('文件上传失败')
  }
  return ticket.file_url
}

async function loadImageElement(url: string) {
  return await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('图片加载失败，无法生成四宫格'))
    image.src = url
  })
}

async function ensureProductCollageImageUrl() {
  if (!isProductIntroScene.value) {
    return selectedFusionImageUrl.value
  }
  if (selectedGalleryImageUrls.value.length !== 4) {
    throw new Error('请先准确选择 4 张图片组成四宫格')
  }
  const images = await Promise.all(selectedGalleryImageUrls.value.map((url) => loadImageElement(url)))
  const canvasSpec = salesAspectRatio.value === '9:16'
    ? { width: 720, height: 1280 }
    : salesAspectRatio.value === '3:4'
      ? { width: 768, height: 1024 }
      : { width: 1024, height: 1024 }
  const cellWidth = canvasSpec.width / 2
  const cellHeight = canvasSpec.height / 2
  const canvas = document.createElement('canvas')
  canvas.width = canvasSpec.width
  canvas.height = canvasSpec.height
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('浏览器不支持四宫格画布生成')
  }
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvasSpec.width, canvasSpec.height)
  images.forEach((image, index) => {
    const col = index % 2
    const row = Math.floor(index / 2)
    const scale = Math.max(cellWidth / image.naturalWidth, cellHeight / image.naturalHeight)
    const drawWidth = image.naturalWidth * scale
    const drawHeight = image.naturalHeight * scale
    const offsetX = col * cellWidth + (cellWidth - drawWidth) / 2
    const offsetY = row * cellHeight + (cellHeight - drawHeight) / 2
    ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight)
  })
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
  if (!blob) {
    throw new Error('四宫格图片导出失败')
  }
  const file = new File([blob], `product-collage-${Date.now()}.png`, { type: 'image/png' })
  productCollageImageUrl.value = await uploadFileToObjectStorage(file, 'digital_human', 'image')
  return productCollageImageUrl.value
}

async function persistDigitalHumanAsset(fileUrl: string, mediaType: 'image' | 'video') {
  if (!draftId.value) {
    await saveDraftNow()
  }
  if (!draftId.value) {
    throw new Error('请先完成前面步骤并生成草稿后，再上传数字人素材')
  }

  const payload: DigitalHumanAssetUpdatePayload = {
    media_type: mediaType,
    file_url: fileUrl,
    human_type: mediaType,
  }

  const saved = await request<AvatarSalesDraftRead>(`${currentDraftApiBase.value}/${draftId.value}/digital-human-asset`, {
    method: 'POST',
    body: payload,
  })
  draftId.value = saved.draft_id
  await applyDraftToView(saved)
}

async function loadBackgroundAssets() {
  if (backgroundAssetsLoading.value) return
  backgroundAssetsLoading.value = true
  try {
    const mediaType = backgroundMode.value === 'video_fill'
      ? 'video'
      : backgroundMode.value === 'image_fill'
        ? 'image'
        : undefined
    const query = mediaType ? `?media_type=${mediaType}` : ''
    const data = await request<BackgroundAssetListResponse>(`/api/v1/background-assets${query}`)
    backgroundAssets.value = data.items || []
  } catch (error) {
    console.error('Failed to load background assets', error)
    window.alert(error instanceof Error ? error.message : '背景素材加载失败')
  } finally {
    backgroundAssetsLoading.value = false
  }
}

async function openBackgroundLibrary() {
  showBackgroundLibrary.value = true
  await loadBackgroundAssets()
}

function closeBackgroundLibrary() {
  showBackgroundLibrary.value = false
}

async function selectBuiltInBackground(mode: 'original') {
  backgroundMode.value = mode
  backgroundAssetId.value = null
  backgroundAssetName.value = ''
  backgroundAssetUrl.value = ''
  await saveDraftNow()
  closeBackgroundLibrary()
}

async function switchBackgroundMediaType(mode: 'image_fill' | 'video_fill') {
  backgroundMode.value = mode
  backgroundAssetId.value = null
  backgroundAssetName.value = ''
  backgroundAssetUrl.value = ''
  await loadBackgroundAssets()
}

async function applyBackgroundAsset(asset: BackgroundAssetRead) {
  backgroundMode.value = asset.media_type === 'video' ? 'video_fill' : 'image_fill'
  backgroundAssetId.value = asset.id
  backgroundAssetName.value = asset.name
  backgroundAssetUrl.value = asset.asset_url
  await saveDraftNow()
  closeBackgroundLibrary()
}

async function uploadRemoteAudioToObjectStorage(sourceUrl: string) {
  const response = await fetch(sourceUrl)
  if (!response.ok) {
    throw new Error('生成音频下载失败')
  }

  const blob = await response.blob()
  const contentType = blob.type || 'audio/mpeg'
  const extension = contentType.includes('wav')
    ? 'wav'
    : contentType.includes('mpeg') || contentType.includes('mp3')
      ? 'mp3'
      : 'mp3'
  const file = new File([blob], `tts_${Date.now()}.${extension}`, { type: contentType })
  return uploadFileToObjectStorage(file, 'digital_human', 'audio')
}

async function uploadRemoteVideoToObjectStorage(sourceUrl: string) {
  const response = await fetch(sourceUrl)
  if (!response.ok) {
    throw new Error('数字人成片下载失败')
  }

  const blob = await response.blob()
  const contentType = blob.type || 'video/mp4'
  const extension = contentType.includes('quicktime')
    ? 'mov'
    : contentType.includes('webm')
      ? 'webm'
      : 'mp4'
  const file = new File([blob], `digital_human_${Date.now()}.${extension}`, { type: contentType })
  return uploadFileToObjectStorage(file, 'digital_human', 'video')
}

function findMatchingDigitalHumanTask() {
  const byTaskNo = digitalHumanTaskId.value.trim()
  if (byTaskNo) {
    return taskStore.findTask(byTaskNo)
  }
  const byDraftId = draftId.value.trim()
  if (!byDraftId) {
    return null
  }
  return [...taskStore.activeTasks, ...taskStore.recentTasks].find((task) => (
    task.taskDomain === 'avatar_video'
    && task.draftId === byDraftId
  )) || null
}

async function finalizeDigitalHumanTask(task: AsyncTask) {
  if (task.status !== 'completed' || !task.resultUrl || finalizedDigitalHumanTaskNo.value === task.taskNo) {
    return
  }
  finalizedDigitalHumanTaskNo.value = task.taskNo
  try {
    const persistedVideoUrl = await uploadRemoteVideoToObjectStorage(task.resultUrl)
    generatedVideoUrl.value = persistedVideoUrl
    generatedVideoSourceUrl.value = task.resultUrl
    digitalHumanTaskId.value = task.taskNo
    digitalHumanTaskStatus.value = task.taskStatus || 'SUCCEEDED'
    generatingDigitalHuman.value = false
    await saveDraftNow()
  } catch (error) {
    finalizedDigitalHumanTaskNo.value = ''
    console.error('Failed to finalize digital human task', error)
  }
}

function syncDigitalHumanTaskState() {
  const task = findMatchingDigitalHumanTask()
  if (!task || task.taskDomain !== 'avatar_video') return

  digitalHumanTaskId.value = task.taskNo

  if (task.status === 'running') {
    generatingDigitalHuman.value = true
    if (task.taskStatus) {
      digitalHumanTaskStatus.value = task.taskStatus
    }
    return
  }

  if (task.status === 'failed') {
    generatingDigitalHuman.value = false
    digitalHumanTaskStatus.value = task.taskStatus || 'FAILED'
    return
  }

  void finalizeDigitalHumanTask(task)
}

function findMatchingFusionTask() {
  const byTaskNo = fusionTaskId.value.trim()
  if (byTaskNo) {
    return taskStore.findTask(byTaskNo)
  }
  const byDraftId = draftId.value.trim()
  if (!byDraftId) {
    return null
  }
  return [...taskStore.activeTasks, ...taskStore.recentTasks].find((task) => (
    task.taskDomain === 'avatar_gallery'
    && task.draftId === byDraftId
  )) || null
}

async function finalizeFusionTask(task: AsyncTask) {
  if (task.status !== 'completed' || finalizedFusionTaskNo.value === task.taskNo) {
    return
  }
  const items = normalizeFusionImages((task.resultUrls || []).map((url) => ({ url, output_type: 'image' })))
  if (!items.length) {
    return
  }
  finalizedFusionTaskNo.value = task.taskNo
  try {
    await applyFusionImages(items)
    fusionTaskId.value = task.taskNo
    fusionTaskStatus.value = task.taskStatus || 'SUCCEEDED'
    fusionGenerating.value = false
  } catch (error) {
    finalizedFusionTaskNo.value = ''
    console.error('Failed to finalize fusion task', error)
  }
}

function syncFusionTaskState() {
  const task = findMatchingFusionTask()
  if (!task || task.taskDomain !== 'avatar_gallery') return

  fusionTaskId.value = task.taskNo

  if (task.status === 'running') {
    fusionGenerating.value = true
    if (task.taskStatus) {
      fusionTaskStatus.value = task.taskStatus
    }
    return
  }

  if (task.status === 'failed') {
    fusionGenerating.value = false
    fusionTaskStatus.value = task.taskStatus || 'FAILED'
    return
  }

  void finalizeFusionTask(task)
}

async function handleImageFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!file.type.startsWith('image/')) {
    window.alert('请选择图片文件')
    return
  }

  imageUploading.value = true
  try {
    const fileUrl = await uploadFileToObjectStorage(file, 'digital_human', 'image')
    humanType.value = 'image'
    digitalHumanImageUrl.value = fileUrl
    await persistDigitalHumanAsset(fileUrl, 'image')
  } catch (error) {
    const message = error instanceof Error ? error.message : '图片上传失败'
    window.alert(message)
  } finally {
    imageUploading.value = false
  }
}

async function handleVideoFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!file.type.startsWith('video/')) {
    window.alert('请选择视频文件')
    return
  }

  videoUploading.value = true
  try {
    const fileUrl = await uploadFileToObjectStorage(file, 'digital_human', 'video')
    humanType.value = 'video'
    digitalHumanVideoUrl.value = fileUrl
    await persistDigitalHumanAsset(fileUrl, 'video')
  } catch (error) {
    const message = error instanceof Error ? error.message : '视频上传失败'
    window.alert(message)
  } finally {
    videoUploading.value = false
  }
}

function normalizeFusionImages(items: GalleryImageItem[], expectedCount: number = Number(salesImageCount.value) || 0) {
  const cleaned = items.filter((item) => Boolean(item?.url))
  if (expectedCount > 0 && cleaned.length > expectedCount) {
    return cleaned.slice(0, expectedCount)
  }
  return cleaned
}

async function persistRemoteFusionImage(image: GalleryImageItem, index: number) {
  const response = await fetch(image.url)
  if (!response.ok) {
    throw new Error(`第 ${index + 1} 张融合图下载失败`)
  }
  const blob = await response.blob()
  const contentType = blob.type || response.headers.get('content-type') || 'image/png'
  const extension = contentType.includes('webp')
    ? 'webp'
    : contentType.includes('jpeg') || contentType.includes('jpg')
      ? 'jpg'
      : 'png'
  const file = new File([blob], `sales-fusion-${Date.now()}-${index + 1}.${extension}`, {
    type: contentType,
  })
  const persistedUrl = await uploadFileToObjectStorage(file, 'digital_human', 'image')
  return {
    ...image,
    url: persistedUrl,
    source_url: image.url,
    persisted: true,
  } as GalleryImageItem
}

async function persistFusionImages(items: GalleryImageItem[]) {
  const persistedItems: GalleryImageItem[] = []
  for (let index = 0; index < items.length; index += 1) {
    const item = items[index]
    if (item.persisted) {
      persistedItems.push(item)
      continue
    }
    persistedItems.push(await persistRemoteFusionImage(item, index))
  }
  return persistedItems
}

async function handleSalesSceneImageChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    window.alert('请上传图片文件')
    return
  }
  salesSceneImageUploading.value = true
  try {
    salesSceneImageUrl.value = await uploadFileToObjectStorage(file, 'digital_human', 'image')
    await saveDraftNow()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '场景图上传失败')
  } finally {
    salesSceneImageUploading.value = false
  }
}

function openFusionPreview(image: GalleryImageItem) {
  fusionPreviewImage.value = image
}

function closeFusionPreview() {
  fusionPreviewImage.value = null
}

function selectFusionImage(image: GalleryImageItem) {
  if (isProductIntroScene.value) {
    const exists = selectedGalleryImageUrls.value.includes(image.url)
    if (exists) {
      selectedGalleryImageUrls.value = selectedGalleryImageUrls.value.filter((item) => item !== image.url)
    } else if (selectedGalleryImageUrls.value.length < 4) {
      selectedGalleryImageUrls.value = [...selectedGalleryImageUrls.value, image.url]
    } else {
      window.alert('产品介绍数字人最多选择 4 张图组成四宫格')
      return
    }
    productCollageImageUrl.value = ''
  }
  selectedFusionImageUrl.value = image.url
}

async function generateProductIntroInstruction(imageUrls: string[]) {
  if (!isProductIntroScene.value) return
  const normalizedImageUrls = imageUrls
    .map((item) => String(item || '').trim())
    .filter((item, index, arr) => Boolean(item) && arr.indexOf(item) === index)
    .slice(0, 4)
  if (!normalizedImageUrls.length) {
    return
  }

  if (!draftId.value) {
    await saveDraftNow()
  }
  if (!draftId.value) {
    throw new Error('草稿保存失败，无法生成产品介绍脚本')
  }

  const runId = instructionGenerationRunId + 1
  instructionGenerationRunId = runId
  instructionGenerating.value = true
  instructionGenerationError.value = ''

  try {
    const data = await request<ProductInstructionGenerateResponse>(`/api/v1/avatar-product-drafts/${draftId.value}/auto-instruction`, {
      method: 'POST',
      body: {
        image_urls: normalizedImageUrls,
        product_name: selectedProductProfile.value?.productName || productKeyword.value.trim() || null,
      },
    })
    if (instructionGenerationRunId !== runId) {
      return
    }
    salesExtraRequirements.value = String(data.generated_instruction || data.draft.extra_requirements || '')
    instructionGenerationError.value = ''
  } catch (error) {
    if (instructionGenerationRunId !== runId) {
      return
    }
    const message = error instanceof ApiError
      ? error.message
      : (error instanceof Error ? error.message : '产品介绍脚本生成失败')
    instructionGenerationError.value = message
    throw new Error(message)
  } finally {
    if (instructionGenerationRunId === runId) {
      instructionGenerating.value = false
    }
  }
}

async function handleRegenerateProductInstruction() {
  if (!fusionImages.value.length) {
    window.alert('请先生成产品融合图')
    return
  }
  try {
    await generateProductIntroInstruction(fusionImages.value.map((item) => item.url))
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '产品介绍脚本生成失败')
  }
}

async function applyFusionImages(items: GalleryImageItem[]) {
  fusionImages.value = normalizeFusionImages(await persistFusionImages(items))
  selectedFusionImageUrl.value = fusionImages.value[0]?.url || ''
  await saveDraftNow()
  if (!isProductIntroScene.value || !fusionImages.value.length) {
    return
  }
  try {
    await generateProductIntroInstruction(fusionImages.value.map((item) => item.url))
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '产品介绍脚本生成失败')
  }
}

async function generateSalesFusionImages() {
  if (!selectedProductProfile.value || !selectedWhiteAsset.value || !selectedWearAsset.value) {
    window.alert('请先完成产品选择，并选中产品白底图和佩戴图')
    return
  }
  if (!digitalHumanImageUrl.value) {
    window.alert('请先在 04 上传数字人图片')
    return
  }

  fusionGenerating.value = true
  fusionImages.value = []
  selectedFusionImageUrl.value = ''
  selectedGalleryImageUrls.value = []
  productCollageImageUrl.value = ''
  if (isProductIntroScene.value) {
    salesExtraRequirements.value = ''
    instructionGenerationError.value = ''
  }
  fusionTaskStatus.value = 'SUBMITTING'

  try {
    await saveDraftNow()
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/model-image-gallery/submit`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        product_name: selectedProductProfile.value.productName,
        product_white_image_url: selectedWhiteAsset.value.assetUrl,
        product_wear_image_url: selectedWearAsset.value.assetUrl,
        model_image_url: digitalHumanImageUrl.value,
        scene_image_url: salesSceneImageUrl.value || null,
        image_count: salesImageCount.value,
        aspect_ratio: salesAspectRatio.value,
        extra_requirements: isProductIntroScene.value ? null : (salesExtraRequirements.value.trim() || null),
      }),
    })
    const data = await parseJsonSafely(response) as { job?: { output?: { task_id?: string; task_status?: string } }; detail?: string } | null
    if (!response.ok) {
      throw new Error(typeof data?.detail === 'string' ? data.detail : '产品融合任务创建失败')
    }
    const submittedFusionTaskId = String(data?.job?.output?.task_id || '')
    const submittedFusionTaskStatus = String(data?.job?.output?.task_status || 'RUNNING')
    if (!submittedFusionTaskId) {
      throw new Error('产品融合任务创建成功但未返回 task_id')
    }
    fusionTaskId.value = submittedFusionTaskId
    fusionTaskStatus.value = submittedFusionTaskStatus
    finalizedFusionTaskNo.value = ''
    stopFusionPolling()
    await saveDraftNow()
    taskStore.addTask({
      taskNo: submittedFusionTaskId,
      keyword: resolvedClipVideoTitle.value,
      platformCode: 'digital_human',
      taskKind: 'avatar_gallery',
      taskDomain: 'avatar_gallery',
      draftId: draftId.value,
      sourceRoutePath: route.path,
      hideWhileOnSource: true,
      purposeScene: videoPurposeScene.value,
      humanType: 'image',
      title: resolvedClipVideoTitle.value,
      taskStatus: submittedFusionTaskStatus,
    })
  } catch (error) {
    fusionGenerating.value = false
    fusionTaskStatus.value = 'FAILED'
    window.alert(error instanceof Error ? error.message : '产品融合失败')
  }
}

function stopFusionPolling() {
  if (fusionTaskTimer) {
    clearTimeout(fusionTaskTimer)
    fusionTaskTimer = null
  }
}

async function pollFusionTask(taskId: string) {
  stopFusionPolling()
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/runninghub/tasks/${taskId}`, {
      method: 'POST',
      headers: buildHeaders(),
    })
    const data = await parseJsonSafely(response) as DigitalHumanTaskResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : '产品融合查询失败')
    }

    const output = data?.output || {}
    fusionTaskStatus.value = String(output.task_status || '')
    const rawResults = output.results
    const results = Array.isArray(rawResults) ? rawResults : rawResults ? [rawResults] : []
    const items = normalizeFusionImages(
      results
        .map((item) => ({
          url: String(item.url || item.video_url || ''),
          output_type: 'image',
        }))
        .filter((item) => Boolean(item.url)),
    )

    if (['SUCCESS', 'SUCCEEDED'].includes(fusionTaskStatus.value.toUpperCase())) {
      await applyFusionImages(items)
      fusionGenerating.value = false
      return
    }

    if (['FAILED', 'CANCELED', 'CANCELLED'].includes(fusionTaskStatus.value.toUpperCase())) {
      fusionGenerating.value = false
      throw new Error(`产品融合失败: ${fusionTaskStatus.value}`)
    }

    fusionTaskTimer = setTimeout(() => {
      void pollFusionTask(taskId)
    }, 5000)
  } catch (error) {
    fusionGenerating.value = false
    fusionTaskStatus.value = 'FAILED'
    window.alert(error instanceof Error ? error.message : '产品融合查询失败')
  }
}

function openBackgroundUpload() {
  if (backgroundUploading.value) return
  if (backgroundMode.value !== 'image_fill' && backgroundMode.value !== 'video_fill') {
    window.alert('当前背景模式无需上传素材')
    return
  }
  backgroundUploadInput.value?.click()
}

function openBgmUpload() {
  if (bgmUploading.value) return
  bgmUploadInput.value?.click()
}

async function clearBgmSelection() {
  bgmMode.value = 'none'
  bgmAssetUrl.value = ''
  await saveDraftNow()
}

async function handleBackgroundFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  const expectVideo = backgroundMode.value === 'video_fill'
  if (expectVideo && !file.type.startsWith('video/')) {
    window.alert('请上传视频作为背景素材')
    return
  }
  if (!expectVideo && !file.type.startsWith('image/')) {
    window.alert('请上传图片作为背景素材')
    return
  }

  const defaultName = file.name.replace(/\.[^.]+$/, '').trim() || (expectVideo ? '新背景视频' : '新背景图片')
  const providedName = window.prompt('请为背景素材命名', defaultName)
  if (providedName === null) {
    return
  }
  const assetName = providedName.trim()
  if (!assetName) {
    window.alert('背景素材名称不能为空')
    return
  }

  backgroundUploading.value = true
  try {
    const fileUrl = await uploadFileToObjectStorage(file, 'clip_background', expectVideo ? 'video' : 'image')
    const asset = await request<BackgroundAssetRead>('/api/v1/background-assets', {
      method: 'POST',
      body: {
        name: assetName,
        media_type: expectVideo ? 'video' : 'image',
        asset_url: fileUrl,
        thumbnail_url: expectVideo ? null : fileUrl,
      },
    })
    backgroundAssetId.value = asset.id
    backgroundAssetName.value = asset.name
    backgroundAssetUrl.value = asset.asset_url
    await loadBackgroundAssets()
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '背景素材上传失败'
    window.alert(message)
  } finally {
    backgroundUploading.value = false
  }
}

async function deleteBackgroundAsset(asset: BackgroundAssetRead) {
  if (asset.source_type === 'official') return
  if (!window.confirm(`确认删除背景素材“${asset.name}”吗？`)) {
    return
  }
  try {
    await request(`/api/v1/background-assets/${asset.id}`, {
      method: 'DELETE',
    })
    if (backgroundAssetId.value === asset.id) {
      backgroundAssetId.value = null
      backgroundAssetName.value = ''
      backgroundAssetUrl.value = ''
      backgroundMode.value = 'original'
      await saveDraftNow()
    }
    await loadBackgroundAssets()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '删除背景素材失败')
  }
}

async function handleBgmFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!file.type.startsWith('audio/')) {
    window.alert('请上传音频文件')
    return
  }

  bgmUploading.value = true
  try {
    bgmAssetUrl.value = await uploadFileToObjectStorage(file, 'clip_bgm', 'audio')
    bgmMode.value = 'uploaded'
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '背景音乐上传失败'
    window.alert(message)
  } finally {
    bgmUploading.value = false
  }
}

async function loadVoiceOptions(preferredVoiceAssetId?: string) {
  voiceListLoading.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/tts/voices?page=1&page_size=100&status=enabled`, {
      method: 'GET',
      headers: buildHeaders(),
    })
    const data = (await parseJsonSafely(response)) as TtsVoiceListResponse | { detail?: string } | null
    if (!response.ok) {
      const message = data && typeof data === 'object' && 'detail' in data && data.detail
        ? data.detail
        : '音色列表加载失败'
      throw new Error(message)
    }

    voiceOptions.value = (data?.data?.list || []).filter((item) => item.status === 'enabled')
    const preferredId = preferredVoiceAssetId || selectedVoiceAssetId.value
    const preferredVoice = preferredId
      ? voiceOptions.value.find((item) => String(item.id) === preferredId)
      : null
    if (preferredVoice) {
      selectedVoiceAssetId.value = String(preferredVoice.id)
      selectedVoiceId.value = String(preferredVoice.third_party_voice_id || '')
      voiceProfile.value = preferredVoice.voice_name
    } else if (voiceOptions.value.length) {
      const first = voiceOptions.value[0]
      selectedVoiceAssetId.value = String(first.id)
      selectedVoiceId.value = String(first.third_party_voice_id || '')
      voiceProfile.value = first.voice_name
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '音色列表加载失败'
    window.alert(message)
  } finally {
    voiceListLoading.value = false
  }
}

function openCloneAudioUpload() {
  if (cloneUploading.value || cloningVoice.value) return
  cloneAudioUploadInput.value?.click()
}

async function handleCloneAudioFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('audio/')) {
    window.alert('请选择音频文件')
    return
  }

  cloneUploading.value = true
  try {
    cloneAudioUrl.value = await uploadFileToObjectStorage(file, 'voice_clone', 'audio')
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '参考音频上传失败'
    window.alert(message)
  } finally {
    cloneUploading.value = false
  }
}

async function waitForClonedVoiceReady(voiceId: string, voiceAssetId?: string) {
  const maxAttempts = 12
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/tts/voices/${voiceId}`, {
      method: 'GET',
      headers: buildHeaders(),
    })
    const data = (await parseJsonSafely(response)) as TtsVoiceDetailResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : '复刻音色状态查询失败')
    }

    const voiceAsset = data?.data?.voice_asset
    const status = String(voiceAsset?.status || '')
    if (['enabled', 'ok'].includes(status.toLowerCase())) {
      await loadVoiceOptions(voiceAssetId)
      return voiceAsset
    }
    if (['failed', 'disabled'].includes(status.toLowerCase())) {
      throw new Error(`复刻音色创建失败，当前状态：${status}`)
    }

    await new Promise((resolve) => {
      window.setTimeout(resolve, 5000)
    })
  }
  return null
}

async function handleCloneVoice() {
  if (cloningVoice.value) return
  if (!cloneVoicePrefix.value.trim()) {
    window.alert('请先填写音色名称')
    return
  }
  if (!/^[a-z0-9]+$/i.test(cloneVoicePrefix.value.trim())) {
    window.alert('音色名称仅允许数字和英文字母')
    return
  }
  if (!cloneAudioUrl.value) {
    window.alert('请先上传参考音频')
    return
  }

  cloningVoice.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/tts/voices/clone`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        target_model: 'cosyvoice-v3.5-plus',
        prefix: cloneVoicePrefix.value.trim().toLowerCase(),
        audio_url: cloneAudioUrl.value,
        language: 'zh',
        max_prompt_audio_length: 20,
        enable_preprocess: true,
        enrollment_config_name: 'voice-enrollment',
      }),
    })

    const data = (await parseJsonSafely(response)) as TtsCloneResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : '复刻音色创建失败')
    }

    const createdVoiceAssetId = data?.data?.id ? String(data.data.id) : ''
    if (createdVoiceAssetId) {
      selectedVoiceAssetId.value = createdVoiceAssetId
    }
    if (data?.data?.voice_id) {
      selectedVoiceId.value = data.data.voice_id
    }

    const voiceId = String(data?.data?.voice_id || '')
    if (voiceId) {
      const readyAsset = await waitForClonedVoiceReady(voiceId, createdVoiceAssetId || undefined)
      if (readyAsset) {
        voiceMode.value = 'clone'
        showCloneCreator.value = false
        selectedVoiceAssetId.value = String(readyAsset.id)
        selectedVoiceId.value = String(readyAsset.third_party_voice_id || voiceId)
        voiceProfile.value = readyAsset.voice_name
        await saveDraftNow()
        window.alert('复刻音色已创建完成，已自动加入当前用户音色列表。')
        return
      }
    }

    await saveDraftNow()
    window.alert('复刻音色已提交创建，但暂时还在部署中。稍后点击“刷新音色”即可查看。')
  } catch (error) {
    const message = error instanceof Error ? error.message : '复刻音色创建失败'
    window.alert(message)
  } finally {
    cloningVoice.value = false
  }
}

function selectCloneVoice(voice: TtsVoiceOption | null) {
  if (voice) {
    selectedVoiceAssetId.value = String(voice.id)
    selectedVoiceId.value = String(voice.third_party_voice_id || '')
    voiceProfile.value = voice.voice_name
  } else {
    selectedVoiceAssetId.value = ''
    selectedVoiceId.value = ''
    voiceProfile.value = ''
  }
  showCloneVoiceMenu.value = false
}

async function handleDeleteVoice(voice: TtsVoiceOption) {
  if (deletingVoice.value) return
  const voiceId = String(voice.third_party_voice_id || '').trim()
  if (!voiceId) {
    window.alert('当前音色缺少 voice_id，无法删除')
    return
  }

  const confirmed = window.confirm(`确认删除音色“${voice.voice_name}”吗？删除后不可恢复。`)
  if (!confirmed) return

  deletingVoice.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/tts/voices/${encodeURIComponent(voiceId)}?enrollment_config_name=voice-enrollment`, {
      method: 'DELETE',
      headers: buildHeaders(),
    })
    const data = (await parseJsonSafely(response)) as { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : '删除音色失败')
    }

    if (selectedVoiceAssetId.value === String(voice.id)) {
      selectedVoiceAssetId.value = ''
      selectedVoiceId.value = ''
      voiceProfile.value = ''
    }
    showCloneVoiceMenu.value = false
    await loadVoiceOptions()
    await saveDraftNow()
    window.alert('音色已删除')
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除音色失败'
    window.alert(message)
  } finally {
    deletingVoice.value = false
  }
}

async function handleGenerateVoice() {
  if (generatingVoice.value) return
  if (!rewrittenCopy.value.trim()) {
    window.alert('请先完成文案改写，再生成口播音频')
    return
  }
  if (!selectedVoiceAssetId.value) {
    window.alert(voiceMode.value === 'clone' ? '请先选择我的音色，或先添加新的复刻音色' : '请先选择系统音色')
    return
  }

  generatingVoice.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/tts/generate`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        draft_id: draftId.value ? Number(draftId.value) : null,
        voice_asset_id: Number(selectedVoiceAssetId.value),
        text: rewrittenCopy.value.trim(),
        style: voiceStyle.value,
        speed: voiceSpeed.value,
        volume: Math.max(voiceSimilarity.value, 0.1),
        pitch: 1.0,
        language: 'zh',
        audio_format: 'mp3',
        tts_config_name: selectedVoiceOption.value?.target_model || 'cosyvoice-v3-flash',
      }),
    })

    const data = (await parseJsonSafely(response)) as TtsGenerateResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      const message = typeof detail === 'string'
        ? detail
        : detail
          ? JSON.stringify(detail)
          : '音频生成失败'
      throw new Error(message)
    }

    const providerAudioUrl = data?.data?.audio_url || ''
    const localAudioUrl = data?.data?.local_audio_url || providerAudioUrl
    if (!localAudioUrl) {
      throw new Error('音频生成成功但未返回可上传地址')
    }

    const minioAudioUrl = await uploadRemoteAudioToObjectStorage(localAudioUrl)
    generatedAudioUrl.value = minioAudioUrl
    generatedAudioLocalUrl.value = localAudioUrl
    generatedAudioSourceUrl.value = providerAudioUrl
    generatedVoiceRecordId.value = data?.data?.record_id ?? null
    selectedVoiceId.value = data?.data?.voice_id || selectedVoiceId.value
    voiceProfile.value = selectedVoiceOption.value?.voice_name || voiceProfile.value
    generatedAudioDurationSeconds.value = 0
    voiceTimelineSegments.value = []
    await syncVoiceTimelineFromGeneratedAudio()
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '音频生成失败'
    window.alert(message)
  } finally {
    generatingVoice.value = false
  }
}

function stopDigitalHumanPolling() {
  if (digitalHumanTaskTimer) {
    clearTimeout(digitalHumanTaskTimer)
    digitalHumanTaskTimer = null
  }
}

async function pollDigitalHumanTask(taskId: string, type: 'image' | 'video' = humanType.value) {
  stopDigitalHumanPolling()
  try {
    const endpoint = type === 'video'
      ? `${copywritingApiBaseUrl}/api/v1/digital-human/videoretalk/tasks/${taskId}`
      : `${copywritingApiBaseUrl}/api/v1/digital-human/s2v/tasks/${taskId}`
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: buildHeaders(),
    })
    const data = (await parseJsonSafely(response)) as DigitalHumanTaskResponse | { detail?: string } | null
    if (!response.ok) {
      const message = data && typeof data === 'object' && 'detail' in data && data.detail
        ? data.detail
        : '数字人任务查询失败'
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
    }

    const output = data?.output || {}
    digitalHumanTaskStatus.value = String(output.task_status || '')
    const results = output.results
    const resultUrl = output.video_url
      || (Array.isArray(results) ? results[0]?.video_url || results[0]?.url : results?.video_url || results?.url)
      || ''
    if (resultUrl) {
      const minioVideoUrl = await uploadRemoteVideoToObjectStorage(resultUrl)
      generatedVideoUrl.value = minioVideoUrl
      generatedVideoSourceUrl.value = resultUrl
      generatingDigitalHuman.value = false
      await saveDraftNow()
      return
    }

    if (['FAILED', 'CANCELED', 'CANCELLED'].includes(digitalHumanTaskStatus.value.toUpperCase())) {
      generatingDigitalHuman.value = false
      await saveDraftNow()
      window.alert(`数字人视频生成失败，当前状态：${digitalHumanTaskStatus.value}`)
      return
    }

    if (['SUCCEEDED', 'SUCCESS'].includes(digitalHumanTaskStatus.value.toUpperCase())) {
      generatingDigitalHuman.value = false
      await saveDraftNow()
      return
    }

    digitalHumanTaskTimer = setTimeout(() => {
      void pollDigitalHumanTask(taskId, type)
    }, 5000)
  } catch (error) {
    generatingDigitalHuman.value = false
    const message = error instanceof Error ? error.message : '数字人任务查询失败'
    window.alert(message)
  }
}

async function handleGenerateDigitalHumanVideo() {
  if (generatingDigitalHuman.value) return
  if (!digitalHumanImageUrl.value) {
    window.alert('请先在 04 上传图片数字人素材')
    return
  }
  if (!selectedFusionImageUrl.value) {
    window.alert(isProductIntroScene.value ? '请先生成产品图，并至少选中一张图片' : '请先在 05 完成产品融合，并选中一张融合图')
    return
  }
  if (sceneRequiresAudio.value && !generatedAudioUrl.value) {
    window.alert('请先在 03 生成口播音频')
    return
  }
  if (isProductIntroScene.value && instructionGenerating.value) {
    window.alert('AI 正在生成产品介绍脚本，请稍后再试')
    return
  }
  const productInstructionText = salesExtraRequirements.value.trim()
  const videoScriptText = isProductIntroScene.value
    ? productInstructionText
    : (rewrittenCopy.value.trim() || productInstructionText)
  if (isProductIntroScene.value && !videoScriptText) {
    window.alert('请先生成产品融合图，等待 AI 自动生成工作流文案')
    return
  }
  generatingDigitalHuman.value = true
  generatedVideoUrl.value = ''
  generatedVideoSourceUrl.value = ''
  digitalHumanTaskStatus.value = 'SUBMITTING'

  try {
    const drivingImageUrl = isProductIntroScene.value
      ? await ensureProductCollageImageUrl()
      : selectedFusionImageUrl.value
    const outputSpec = await resolveDigitalHumanOutputSpec()
    const endpoint = `${copywritingApiBaseUrl}/api/v1/digital-human/s2v/submit`
    const payload = {
      image_url: drivingImageUrl,
      audio_url: sceneRequiresAudio.value ? generatedAudioUrl.value : null,
      script_text: videoScriptText,
      aspect_ratio: outputSpec.aspectRatio,
      resolution: outputSpec.resolution,
      style: 'speech',
      skip_detect: false,
      purpose_scene: videoPurposeScene.value,
    }
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    })

    const data = (await parseJsonSafely(response)) as DigitalHumanSubmitResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : '数字人视频生成失败')
    }

    const taskId = String(data?.job?.output?.task_id || '')
    const taskStatus = String(data?.job?.output?.task_status || '')
    if (!taskId) {
      throw new Error('数字人任务创建成功但未返回 task_id')
    }

    digitalHumanTaskId.value = taskId
    digitalHumanTaskStatus.value = taskStatus || 'PENDING'
    finalizedDigitalHumanTaskNo.value = ''
    await saveDraftNow()
    taskStore.addTask({
      taskNo: taskId,
      keyword: resolvedClipVideoTitle.value,
      platformCode: 'digital_human',
      taskKind: 'avatar_video',
      taskDomain: 'avatar_video',
      draftId: draftId.value,
      sourceRoutePath: route.path,
      hideWhileOnSource: true,
      purposeScene: videoPurposeScene.value,
      humanType: 'image',
      title: resolvedClipVideoTitle.value,
      taskStatus: digitalHumanTaskStatus.value,
    })
  } catch (error) {
    generatingDigitalHuman.value = false
    const message = error instanceof Error ? error.message : '数字人视频生成失败'
    window.alert(message)
  }
}

async function copyTranscriptSrt() {
  const s = extractResult.value?.transcript_srt
  if (!s?.trim()) {
    window.alert('当前没有可用的原片 SRT，请先完成带转录的提取')
    return
  }
  try {
    await navigator.clipboard.writeText(s)
    window.alert('已复制原片 ASR 字幕（SRT）到剪贴板')
  } catch {
    window.alert('复制失败，请手动从网络响应中复制 transcript_srt')
  }
}

async function handleExtractCopy() {
  if (extractingCopy.value) return
  if (!sourceUrl.value.trim()) {
    window.alert('请先输入视频链接')
    return
  }

  extractingCopy.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/copywriting/extract`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({ url: sourceUrl.value.trim(), include_transcript_srt: true }),
    })

    const data = (await parseJsonSafely(response)) as ExtractCopyResponse | { detail?: string } | null
    if (!response.ok) {
      const message = data && typeof data === 'object' && 'detail' in data && data.detail
        ? data.detail
        : '文案提取失败'
      throw new Error(message)
    }

    extractResult.value = data as ExtractCopyResponse
    rewriteResult.value = null
    sourceCopy.value = extractResult.value.extracted_copy || ''
    rewrittenCopy.value = ''
    if (!clipVideoTitle.value.trim()) {
      const titleFromContent = (extractResult.value.content_info?.title || '').trim()
      if (titleFromContent) {
        clipVideoTitle.value = titleFromContent
      } else if (sourceCopy.value.trim()) {
        clipVideoTitle.value = sourceCopy.value.trim().slice(0, 30)
      }
    }
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '文案提取失败'
    window.alert(message)
  } finally {
    extractingCopy.value = false
  }
}

async function rewriteCopyWithInstruction(instruction: string) {
  if (rewritingCopy.value) return
  if (!sourceCopy.value.trim()) {
    window.alert('请先提取或输入原始文案')
    return
  }

  rewritingCopy.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/copywriting/rewrite`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        text: sourceCopy.value.trim(),
        instruction,
      }),
    })

    const data = (await parseJsonSafely(response)) as RewriteCopyResponse | { detail?: string } | null
    if (!response.ok) {
      const message = data && typeof data === 'object' && 'detail' in data && data.detail
        ? data.detail
        : '文案改写失败'
      throw new Error(message)
    }

    rewriteResult.value = data as RewriteCopyResponse
    rewrittenCopy.value = rewriteResult.value.rewritten_text || ''
    if (!clipVideoTitle.value.trim() && !(extractResult.value?.content_info?.title || '').trim() && rewrittenCopy.value.trim()) {
      clipVideoTitle.value = rewrittenCopy.value.trim().slice(0, 30)
    }
    await saveDraftNow()
  } catch (error) {
    const message = error instanceof Error ? error.message : '文案改写失败'
    window.alert(message)
  } finally {
    rewritingCopy.value = false
  }
}

async function handleRewriteCopy() {
  await rewriteCopyWithInstruction(buildRewriteInstruction())
}

async function handleOptimizeRewrite() {
  await rewriteCopyWithInstruction(buildRewriteInstruction('进一步压缩冗余，让句子更顺、更像真人口播'))
}

watch(
  [
    sourceUrl,
    sourceCopy,
    rewrittenCopy,
    voiceMode,
    selectedVoiceAssetId,
    voiceProfile,
    voiceStyle,
    voiceSpeedSlider,
    voiceSimilaritySlider,
    cloneAudioUrl,
    cloneVoicePrefix,
    generatedAudioSourceUrl,
    humanType,
    digitalTemplate,
    digitalScene,
    videoPurposeScene,
    productKeyword,
    selectedProductId,
    selectedWhiteImageId,
    selectedWearImageId,
    salesSceneImageUrl,
    salesImageCount,
    salesAspectRatio,
    salesExtraRequirements,
    fusionTaskId,
    fusionTaskStatus,
    selectedFusionImageUrl,
    generatedVideoUrl,
    digitalHumanTaskId,
    digitalHumanTaskStatus,
    subtitleSettingsEnabled,
    subtitleMode,
    subtitleFontSizeSlider,
    subtitleOffsetYSlider,
    subtitleAlign,
    backgroundMode,
    backgroundAssetUrl,
    clipTemplate,
    selectedClipTemplate,
    titleTemplate,
    clipVideoTitle,
    overlaySubtitle,
    overlayTag,
    bgmMode,
    bgmAssetUrl,
    voiceVolumeSlider,
    bgmVolumeSlider,
    productCollageImageUrl,
    () => selectedGalleryImageUrls.value.join('|'),
    () => fusionImages.value.map((item) => item.url).join('|'),
  ],
  () => {
    scheduleDraftSave()
  },
)

watch(backgroundMode, (mode, previousMode) => {
  if (mode === previousMode) return
  if (mode === 'original') {
    backgroundAssetId.value = null
    backgroundAssetName.value = ''
    backgroundAssetUrl.value = ''
    return
  }
  if ((mode === 'image_fill' || mode === 'video_fill') && previousMode && mode !== previousMode) {
    backgroundAssetId.value = null
    backgroundAssetName.value = ''
    backgroundAssetUrl.value = ''
  }
})

watch(titleTemplate, (value) => {
  const option = titleTemplateOptions.find((item) => item.value === value) ?? titleTemplateOptions[0]
  if (!option.supportsSubtitle) {
    overlaySubtitle.value = ''
  }
  if (!option.supportsTag) {
    overlayTag.value = ''
  }
})

watch(selectedVoiceOption, (voice) => {
  if (!voice) return
  selectedVoiceId.value = String(voice.third_party_voice_id || '')
  voiceProfile.value = voice.voice_name
})

watch(voiceMode, (mode) => {
  showCloneCreator.value = false
  const options = mode === 'clone' ? userVoiceOptions.value : systemVoiceOptions.value
  if (!options.length) {
    selectedVoiceAssetId.value = ''
    selectedVoiceId.value = ''
    return
  }
  const currentExists = options.some((item) => String(item.id) === selectedVoiceAssetId.value)
  if (!currentExists) {
    const first = options[0]
    selectedVoiceAssetId.value = String(first.id)
    selectedVoiceId.value = String(first.third_party_voice_id || '')
    voiceProfile.value = first.voice_name
  }
})

watch(voiceOptions, () => {
  const options = voiceMode.value === 'clone' ? userVoiceOptions.value : systemVoiceOptions.value
  if (!options.length) {
    if (!selectedVoiceOption.value) {
      selectedVoiceAssetId.value = ''
      selectedVoiceId.value = ''
    }
    return
  }
  const currentExists = options.some((item) => String(item.id) === selectedVoiceAssetId.value)
  if (!currentExists) {
    const first = options[0]
    selectedVoiceAssetId.value = String(first.id)
    selectedVoiceId.value = String(first.third_party_voice_id || '')
    voiceProfile.value = first.voice_name
  }
})

watch(generatedAudioUrl, (url) => {
  if (!url) {
    generatedAudioDurationSeconds.value = 0
    return
  }
  void getAudioDurationSeconds(url)
    .then((duration) => {
      if (generatedAudioUrl.value === url) {
        generatedAudioDurationSeconds.value = duration
      }
    })
    .catch(() => {
      if (generatedAudioUrl.value === url) {
        generatedAudioDurationSeconds.value = 0
      }
    })
})

watch(
  () => [generatedVideoUrl.value, generatedVideoSourceUrl.value, digitalHumanImageUrl.value] as const,
  ([videoUrl, sourceUrl]) => {
    const previewVideo = [videoUrl, sourceUrl]
      .map((item) => (typeof item === 'string' ? item.trim() : ''))
      .find(Boolean)
    if (previewVideo) {
      void extractPreviewFrame(previewVideo)
      return
    }
    previewFrameRequestId += 1
    previewFrameDataUrl.value = ''
    previewFrameWidth.value = 0
    previewFrameHeight.value = 0
    previewFrameLoading.value = false
  },
  { immediate: true },
)

watch(
  () => [props.purposeScene, props.purposeLocked] as const,
  ([scene, locked]) => {
    if (switchingScene.value || hydratingDraft.value) return
    if (scene && (locked || !videoPurposeScene.value)) {
      videoPurposeScene.value = scene
    }
  },
  { immediate: true },
)

watch(videoPurposeScene, async (scene, previous) => {
  if (purposeLocked.value || hydratingDraft.value || switchingScene.value || !scene || !previous || scene === previous) return
  await handleSceneSwitch(scene, previous)
})

watch(
  () => [
    draftId.value,
    fusionTaskId.value,
    digitalHumanTaskId.value,
    taskStore.activeTasks.map((task) => `${task.taskNo}:${task.status}:${task.taskStatus}`).join('|'),
    taskStore.recentTasks.map((task) => `${task.taskNo}:${task.status}:${task.taskStatus}`).join('|'),
  ],
  () => {
    syncFusionTaskState()
    syncDigitalHumanTaskState()
  },
)

onMounted(() => {
  clippingVideo.value = false
  clipRenderStage.value = ''
  void loadDraftLibrary()
  void loadVoiceOptions()
  void loadVideoEditTemplates({ silent: true })
  void loadProducts()
  const rawDraftId = route.query.draftId
  if (typeof rawDraftId === 'string' && rawDraftId.trim()) {
    void loadDraft(rawDraftId.trim())
  }
  syncFusionTaskState()
  syncDigitalHumanTaskState()
})

onBeforeUnmount(() => {
  stopFusionPolling()
  stopDigitalHumanPolling()
  if (clipBlobUrl.value) {
    URL.revokeObjectURL(clipBlobUrl.value)
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 0 rgba(148, 163, 184, 0.08);
  margin: -24px -24px 0;
  padding: 16px 28px 15px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-subhead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.field-hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.empty-icon {
  font-size: 38px;
  color: rgba(37, 99, 235, 0.7);
}

.product-asset-picker-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 10px 12px;
  cursor: pointer;
  color: #0f172a;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.product-asset-picker-trigger:hover {
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.06);
}

.product-asset-picker-thumb {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-asset-picker-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-asset-picker-placeholder {
  font-size: 26px;
  color: #94a3b8;
}

.product-asset-picker-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.product-asset-picker-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.product-asset-picker-sub {
  font-size: 12px;
  color: #64748b;
}

.product-asset-picker-chevron {
  flex-shrink: 0;
  font-size: 22px;
  color: #94a3b8;
}

.product-asset-picker-dialog {
  width: min(560px, 100%);
}

.product-asset-picker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 10px;
  max-height: min(52vh, 420px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.product-asset-picker-option {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.product-asset-picker-option:hover {
  border-color: rgba(59, 130, 246, 0.35);
}

.product-asset-picker-option.active {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.1);
}

.product-asset-picker-option img {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 10px;
  background: #e2e8f0;
}

.product-asset-picker-tag {
  font-size: 11px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fusion-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.fusion-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 10px;
  text-align: left;
  cursor: pointer;
}

.fusion-card.active {
  border-color: #2563eb;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
}

.fusion-thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 12px;
  background: #e2e8f0;
}

.fusion-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.image-preview-dialog {
  width: min(880px, 100%);
}

.image-preview-body {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #f8fafc;
}

.image-preview-full {
  max-width: 100%;
  max-height: 72vh;
  object-fit: contain;
  border-radius: 16px;
}

.draft-badge {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
}

.header-purpose-select {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
  max-width: min(260px, 44vw);
}

.header-purpose-select:focus {
  border-color: rgba(37, 99, 235, 0.5);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.header-purpose-text {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  max-width: min(260px, 44vw);
  white-space: nowrap;
}

.draft-library-button {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 0 14px;
  background: #fff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.mode-switch {
  position: relative;
}

.mode-switch-button {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 0 14px;
  background: #fff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.mode-switch-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 120px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 8px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
}

.mode-switch-item {
  min-height: 36px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: #334155;
  text-align: left;
  padding: 0 12px;
  cursor: pointer;
}

.mode-switch-item.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.mode-switch-item:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.draft-library-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.42);
  padding: 24px;
}

.draft-library-dialog {
  width: min(720px, 100%);
  max-height: min(70vh, 760px);
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid #dbeafe;
  background: #fff;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}

.background-library-dialog {
  width: min(1120px, 100%);
}

.background-library-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(70vh - 96px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.background-choice-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.background-upload-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.background-library-sections {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.background-library-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid #dbeafe;
  border-radius: 20px;
  background: #fff;
  padding: 16px;
}

.background-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.background-section-head h4 {
  margin: 0;
  font-size: 15px;
  color: #0f172a;
}

.background-section-head span {
  font-size: 12px;
  color: #64748b;
}

.background-asset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.background-asset-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px;
  text-align: left;
}

.background-asset-select {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 0;
  background: transparent;
  padding: 0;
  text-align: left;
  cursor: pointer;
}

.background-asset-card.active {
  border-color: rgba(59, 130, 246, 0.42);
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.08);
}

.background-asset-card strong {
  color: #0f172a;
  font-size: 14px;
}

.background-asset-card span {
  font-size: 12px;
  color: #64748b;
}

.background-asset-thumb {
  width: 100%;
  min-height: 140px;
  max-height: 240px;
  overflow: auto;
  border-radius: 14px;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.background-asset-thumb img,
.background-asset-thumb video {
  max-width: 100%;
  max-height: 240px;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
}

.background-asset-delete {
  min-height: 36px;
  border: 1px solid #fecaca;
  border-radius: 12px;
  background: #fff5f5;
  color: #dc2626;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.draft-library-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 20px 14px;
  border-bottom: 1px solid #e2e8f0;
}

.draft-library-head h3 {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.draft-library-head p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}

.draft-library-close {
  min-height: 38px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0 14px;
  background: #fff;
  color: #334155;
  cursor: pointer;
}

.draft-library-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.draft-library-secondary {
  min-height: 38px;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  padding: 0 14px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
}

.draft-library-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(70vh - 96px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.draft-library-item {
  display: flex;
  align-items: stretch;
  gap: 10px;
}

.draft-library-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  flex: 1;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  padding: 14px 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  color: #334155;
  text-align: left;
  cursor: pointer;
}

.draft-library-delete {
  min-width: 72px;
  border: 1px solid #fecaca;
  border-radius: 18px;
  background: #fff5f5;
  color: #dc2626;
  cursor: pointer;
}

.draft-library-publish {
  min-width: 72px;
  border: 1px solid #bfdbfe;
  border-radius: 18px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
}

.draft-library-main strong {
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.draft-library-main span {
  font-size: 12px;
  color: #64748b;
}

.draft-library-empty {
  padding: 28px 20px;
  font-size: 14px;
  color: #64748b;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

.grid-layout {
  display: grid;
  gap: 22px;
  align-items: start;
}

.grid-layout-single {
  grid-template-columns: minmax(320px, 1fr);
}

.grid-layout-double {
  grid-template-columns: repeat(2, minmax(320px, 1fr));
}

.grid-layout-triple {
  grid-template-columns: repeat(3, minmax(320px, 1fr));
}

.flow-column,
.studio-column,
.preview-column {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.panel-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-radius: 26px;
  border: 1px solid #dbeafe;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  padding: 20px;
  box-shadow: 0 10px 28px rgba(148, 163, 184, 0.08);
}

.panel-accent {
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.8), transparent 26%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.feature-card {
  position: relative;
  overflow: hidden;
}

.feature-card::after {
  content: "";
  position: absolute;
  inset: auto -20px -34px auto;
  width: 140px;
  height: 140px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(191, 219, 254, 0.35), transparent 68%);
  pointer-events: none;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.panel-head h2 {
  margin: 8px 0 0;
  font-size: 18px;
  line-height: 1.2;
  color: #0f172a;
}

.panel-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.panel-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.panel-tag-button {
  border: 0;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.panel-tag-button:hover {
  background: #dbeafe;
  color: #1e40af;
}


.field-label {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
}

.field-input,
.field-area,
.count-chip {
  width: 100%;
  border-radius: 18px;
  border: 1px solid #dbeafe;
  background: #fff;
  color: #0f172a;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.field-input {
  min-height: 46px;
  padding: 0 16px;
  font-size: 14px;
  outline: none;
}

.field-area {
  resize: vertical;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.75;
  outline: none;
}

.field-input:focus,
.field-area:focus,
select.field-input:focus {
  border-color: rgba(37, 99, 235, 0.5);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.inline-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.voice-select {
  position: relative;
}

.voice-select-trigger {
  display: flex;
  min-height: 46px;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(147, 197, 253, 0.6);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  padding: 0 16px;
  color: #0f172a;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(148, 163, 184, 0.08);
}

.voice-select-menu {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.12);
}

.voice-select-row {
  display: flex;
  align-items: center;
  border-top: 1px solid #e2e8f0;
}

.voice-select-row.active {
  background: #eff6ff;
}

.voice-select-option {
  display: flex;
  min-height: 42px;
  width: 100%;
  align-items: center;
  border: 0;
  background: transparent;
  padding: 0 14px;
  color: #0f172a;
  text-align: left;
  cursor: pointer;
}

.voice-select-option:hover {
  background: #f8fafc;
}

.voice-select-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voice-select-delete {
  display: inline-flex;
  height: 32px;
  width: 32px;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}

.voice-select-delete .material-symbols-outlined {
  font-size: 18px;
}

.voice-select-delete:hover:not(:disabled) {
  background: #fef2f2;
  color: #dc2626;
}

.voice-select-arrow {
  font-size: 20px;
  color: #94a3b8;
}

.primary-button,
.soft-button,
.ghost-button,
.text-link {
  border: 0;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, opacity 0.18s ease;
}

.primary-button {
  min-height: 46px;
  border-radius: 16px;
  padding: 0 18px;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.primary-button:disabled,
.soft-button:disabled,
.ghost-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  box-shadow: none;
}

.soft-button {
  min-height: 46px;
  border-radius: 16px;
  padding: 0 18px;
  background: #eff6ff;
  color: #1d4ed8;
}

.danger-button {
  background: #fef2f2;
  color: #dc2626;
}

.ghost-button {
  min-height: 44px;
  border-radius: 16px;
  padding: 0 16px;
  background: #fff;
  border: 1px solid #bfdbfe;
  color: #2563eb;
}

.text-link {
  min-height: 36px;
  border-radius: 14px;
  padding: 0 12px;
  background: transparent;
  color: #2563eb;
}

.primary-button:hover:not(:disabled),
.soft-button:hover:not(:disabled),
.ghost-button:hover:not(:disabled),
.text-link:hover:not(:disabled) {
  transform: translateY(-1px);
}

.platform-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.platform-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  border-radius: 999px;
  border: 1px solid #dbeafe;
  background: #fff;
  color: #64748b;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 700;
}

.platform-chip.active {
  background: rgba(37, 99, 235, 0.14);
  color: #1d4ed8;
  border-color: rgba(59, 130, 246, 0.28);
}

.hint-text {
  margin-top: -2px;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 10px;
}

.toolbar-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.count-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 92px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
}

.status-card,
.subtitle-card,
.meta-card {
  border-radius: 20px;
  border: 1px solid #dbeafe;
  background: rgba(255, 255, 255, 0.92);
}

.status-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.16);
}

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.slider-block {
  border-radius: 20px;
  border: 1px solid #dbeafe;
  background: #fff;
  padding: 14px 16px;
}

.slider-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: #475569;
}

.upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  border: 1px dashed rgba(59, 130, 246, 0.3);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.82)),
    radial-gradient(circle at top, rgba(191, 219, 254, 0.3), transparent 56%);
  text-align: center;
  padding: 24px;
}

.choice-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.choice-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-height: 130px;
  border-radius: 22px;
  border: 1px solid #dbeafe;
  background: #fff;
  padding: 18px;
  color: #0f172a;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.choice-card span:last-child {
  font-size: 12px;
  color: #64748b;
}

.choice-card.active,
.choice-card:hover {
  border-color: rgba(59, 130, 246, 0.42);
  transform: translateY(-1px);
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.08);
}

.choice-card.disabled {
  opacity: 0.6;
}

.preview-image {
  width: auto;
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 18px;
  border: 1px solid rgba(59, 130, 246, 0.14);
  box-shadow: 0 10px 28px rgba(148, 163, 184, 0.08);
  background: #fff;
  display: block;
}

.edit-panel {
  min-height: 100%;
}

.subtitle-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
}

.radio-row {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #334155;
}

.edit-footer {
  display: flex;
  gap: 10px;
  align-items: center;
}

.preview-card {
  min-height: 100%;
}

.preview-stage {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-screen {
  display: flex;
  min-height: 420px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 30px;
  border: 1px dashed rgba(59, 130, 246, 0.28);
  background:
    radial-gradient(circle at top, rgba(191, 219, 254, 0.4), transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(239, 246, 255, 0.88));
  text-align: center;
  padding: 28px;
}

.preview-video {
  width: 100%;
  max-height: 420px;
  border-radius: 24px;
  object-fit: contain;
  background: #0f172a;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
}

.preview-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.meta-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
  color: #475569;
  font-size: 13px;
}

.meta-card strong {
  color: #0f172a;
  font-size: 16px;
}

.clip-video-title-input {
  height: 46px;
  border-radius: 17px;
  border-color: #d9e8ff;
  background: #fff;
}

.subtitle-setting-shell {
  width: 100%;
  border-radius: 17px;
  background: #fff;
  border: 1px solid #d9e8ff;
  padding: 14px 12px;
}

.subtitle-setting-title {
  margin-bottom: 12px;
  color: #172033;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
}

.subtitle-setting-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  row-gap: 8px;
  color: #172033;
  font-size: 12px;
  white-space: nowrap;
}

.clip-template-runtime-card {
  margin-top: 12px;
}

.clip-template-runtime-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.clip-template-runtime-head strong {
  display: block;
  color: #172033;
  font-size: 14px;
  font-weight: 700;
}

.clip-template-runtime-head p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.clip-template-runtime-title {
  flex: 0 0 auto;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.subtitle-setting-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #34d07c;
}

.subtitle-setting-label {
  color: #172033;
  font-size: 12px;
  font-weight: 600;
}

.subtitle-setting-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 7px;
  border: 1px solid #d9e8ff;
  border-radius: 8px;
  background: #f5f9ff;
  color: #2f6df6;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.subtitle-setting-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.subtitle-setting-btn__icon,
.subtitle-template-tag__icon {
  width: 15px;
  height: 15px;
  border: 1px solid #2f6df6;
  border-radius: 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #2f6df6;
  line-height: 1;
}

.subtitle-template-tag {
  height: 26px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 7px;
  border: 1px solid #d9e8ff;
  border-radius: 8px;
  color: #2f6df6;
  background: #f5f9ff;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.subtitle-template-tag.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.subtitle-template-tag__name,
.subtitle-template-tag__code {
  color: #2f6df6;
}

.subtitle-template-link {
  color: #18aeea;
  font-size: 12px;
  font-weight: 700;
}

.volume-grid-clip {
  gap: 13px;
  margin-bottom: 15px;
}

.clip-slider-card {
  border-radius: 18px;
  border-color: #d9e8ff;
}

.clip-slider-card .slider-row {
  margin-bottom: 14px;
  color: #526176;
  font-size: 14px;
}

.clip-slider-card .slider-row strong {
  color: #374760;
}

.clip-submit-button {
  height: 46px;
  border-radius: 15px;
  font-size: 16px;
  font-weight: 800;
}

.template-live-preview-stage {
  position: relative;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: #0f172a;
  aspect-ratio: 16 / 9;
  min-height: 360px;
}

.template-live-preview-stage--compact {
  min-height: 0;
}

.clip-preview-style-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.clip-preview-style-head > p {
  margin: 0;
}

.clip-preview-expand-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  border: 0;
  border-radius: 10px;
  padding: 6px 10px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.clip-preview-expand-trigger:hover {
  background: rgba(37, 99, 235, 0.14);
  color: #1d4ed8;
}

.clip-preview-expand-trigger .material-symbols-outlined,
.clip-template-card__settings .material-symbols-outlined {
  font-size: 18px;
  line-height: 1;
}

.template-preview-media {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.template-render-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.template-render-text {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
  font-weight: 800;
  paint-order: stroke fill;
  stroke: rgb(0 0 0 / 0.62);
  stroke-width: 3px;
  stroke-linejoin: round;
}

.template-render-title {
  font-weight: 900;
}

.template-render-title-subtitle,
.template-render-subtitle {
  font-weight: 800;
  stroke-width: 2px;
}

.template-preview-empty {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  text-align: center;
  color: #94a3b8;
}

.template-preview-empty .material-symbols-outlined {
  font-size: 32px;
}

.subtitle-settings-dialog {
  width: min(720px, calc(100vw - 40px));
  max-height: min(82vh, 760px);
  display: flex;
  flex-direction: column;
}

.subtitle-settings-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px 20px;
}

.subtitle-settings-body .template-live-preview-stage--compact {
  flex: 0 0 auto;
  max-height: min(48vh, 420px);
}

.segmented-control {
  display: inline-grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  width: 100%;
  border-radius: 16px;
  border: 1px solid #dbeafe;
  background: #f8fbff;
  padding: 4px;
  gap: 4px;
}

.segmented-control__item {
  min-height: 38px;
  border-radius: 12px;
  background: transparent;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.segmented-control__item.active {
  background: #ffffff;
  color: #1d4ed8;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.08);
}

.clip-template-dialog {
  max-width: 1080px;
}

.clip-template-dialog-v2 {
  width: min(1380px, calc(100vw - 64px));
  max-width: none;
  max-height: calc(100vh - 48px);
  overflow: hidden;
}

.clip-template-editor-title {
  min-width: 180px;
  max-width: min(420px, 48vw);
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #0f172a;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  padding: 6px 8px;
  outline: none;
}

.clip-template-editor-title:hover,
.clip-template-editor-title:focus {
  border-color: #bfdbfe;
  background: #f8fbff;
  color: #2563eb;
}

.clip-template-library {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.clip-template-library-v2 {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
  max-height: calc(100vh - 150px);
  overflow: auto;
  padding: 4px 2px 8px;
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.55) transparent;
}

.clip-template-card {
  position: relative;
  border: 1px solid #dbeafe;
  border-radius: 20px;
  background: #fff;
  overflow: hidden;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.clip-template-card:hover,
.clip-template-card.active {
  border-color: rgba(59, 130, 246, 0.42);
  transform: translateY(-1px);
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.08);
}

.clip-template-card-v2 {
  border-radius: 16px;
}

.clip-template-card__preview {
  position: relative;
  aspect-ratio: 9 / 16;
  padding: 18px 14px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.06), rgba(15, 23, 42, 0.2)),
    linear-gradient(135deg, #dbeafe 0%, #eff6ff 45%, #bfdbfe 100%);
}

.clip-template-card-v2 .clip-template-card__preview {
  aspect-ratio: 3 / 5;
  min-height: 300px;
  padding: 16px;
  align-items: stretch;
  justify-content: flex-start;
}

.clip-template-card__body {
  padding: 14px 14px 16px;
}

.clip-template-card-v2 .clip-template-card__body {
  padding: 12px 12px 14px;
  text-align: center;
}

.clip-template-card__body strong {
  display: block;
  color: #0f172a;
  font-size: 15px;
}

.clip-template-card-v2 .clip-template-card__body strong {
  margin: 0;
  font-size: 14px;
}

.clip-template-card__demo-title {
  position: absolute;
  top: 14px;
  left: 14px;
  right: 14px;
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  text-shadow: 0 2px 10px rgba(15, 23, 42, 0.28);
}

.clip-template-card__demo-subtitle {
  position: absolute;
  left: 14px;
  bottom: 14px;
  max-width: calc(100% - 28px);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.76);
  color: #fff;
  padding: 7px 10px;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.35;
}

.clip-template-card__settings {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 4;
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #2563eb;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
}

.clip-template-card__settings:hover {
  background: #eff6ff;
}

.clip-template-card__cover-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.template-preview-manual_subtitle {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(15, 23, 42, 0.08)),
    linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.template-preview-talk_clean {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(15, 23, 42, 0.22)),
    linear-gradient(135deg, #fef3c7 0%, #fde68a 35%, #bfdbfe 100%);
}

.template-preview-talk_brand {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(15, 23, 42, 0.24)),
    linear-gradient(135deg, #fed7aa 0%, #fdba74 30%, #bfdbfe 100%);
}

.template-preview-talk_digital {
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.12), rgba(15, 23, 42, 0.28)),
    linear-gradient(135deg, #c4b5fd 0%, #818cf8 40%, #93c5fd 100%);
}

.template-preview-talk_tag {
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.26)),
    linear-gradient(135deg, #fbcfe8 0%, #f9a8d4 35%, #bfdbfe 100%);
}

.template-preview-talk_gold {
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.28)),
    linear-gradient(135deg, #fde68a 0%, #f59e0b 35%, #c7d2fe 100%);
}

.clip-template-editor-grid {
  display: grid;
  grid-template-columns: 380px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
  max-height: calc(100vh - 150px);
  overflow: hidden;
}

.clip-template-cover-panel,
.clip-template-editor-fields,
.clip-template-section {
  border: 1px solid #dbeafe;
  border-radius: 18px;
  background: #fff;
  padding: 16px;
}

.clip-template-cover-panel {
  position: sticky;
  top: 0;
  align-self: start;
}

.clip-template-cover-panel h4 {
  margin: 0 0 12px;
  color: #0f172a;
  font-size: 15px;
}

.clip-template-cover-box {
  position: relative;
  display: flex;
  width: 100%;
  aspect-ratio: 3 / 5;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px dashed #bfdbfe;
  border-radius: 18px;
  background: #fafcff;
  cursor: pointer;
}

.clip-template-cover-box:disabled {
  cursor: wait;
}

.clip-template-cover-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.clip-template-cover-plus {
  position: relative;
  z-index: 2;
  display: inline-flex;
  width: 56px;
  height: 56px;
  align-items: center;
  justify-content: center;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #fff;
  color: #55749d;
  font-size: 30px;
}

.clip-template-cover-tip {
  position: absolute;
  top: 50%;
  left: calc(50% + 40px);
  z-index: 2;
  transform: translateY(-50%);
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.82);
  color: #fff;
  padding: 6px 12px;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.16s ease;
  white-space: nowrap;
}

.clip-template-cover-box:hover .clip-template-cover-tip {
  opacity: 1;
}

.clip-template-cover-box.has-cover .clip-template-cover-plus {
  display: none;
}

.clip-template-cover-preview {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.clip-template-cover-title,
.clip-template-cover-badge,
.clip-template-cover-subtitle {
  position: absolute;
  z-index: 2;
}

.clip-template-cover-title {
  left: 18px;
  right: 18px;
  color: #fff;
  text-shadow: 0 3px 14px rgba(15, 23, 42, 0.28);
}

.clip-template-cover-title.top-left {
  top: 18px;
  text-align: left;
}

.clip-template-cover-title.top-center {
  top: 18px;
  text-align: center;
}

.clip-template-cover-title.bottom-left {
  bottom: 118px;
  text-align: left;
}

.clip-template-cover-title strong {
  display: block;
  font-size: var(--clip-title-size, 24px);
  line-height: 1.2;
}

.clip-template-cover-title span {
  display: block;
  margin-top: 6px;
  font-size: var(--clip-subtitle-size, 13px);
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.92);
}

.clip-template-cover-badge {
  top: 18px;
  right: 18px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.56);
  color: #fff7d4;
  padding: 6px 10px;
  font-weight: 800;
}

.clip-template-cover-subtitle {
  left: 14px;
  right: 14px;
  bottom: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.clip-template-cover-subtitle.left span {
  margin-right: auto;
  text-align: left;
}

.clip-template-cover-subtitle.center span {
  margin-left: auto;
  margin-right: auto;
  text-align: center;
}

.clip-template-cover-subtitle span {
  display: inline-block;
  max-width: 100%;
  border-radius: 12px;
  padding: 8px 12px;
  line-height: 1.45;
  font-weight: 800;
  word-break: break-word;
}

.clip-template-cover-subtitle.sub-clean span {
  background: transparent;
  color: #fff;
  text-shadow:
    0 2px 6px rgba(15, 23, 42, 0.65),
    0 0 2px rgba(15, 23, 42, 0.95);
}

.clip-template-cover-subtitle.sub-outline span {
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
}

.clip-template-cover-subtitle.sub-highlight span {
  background: rgba(255, 244, 177, 0.96);
  color: #2f2300;
}

.clip-template-cover-subtitle.sub-double span {
  background: rgba(12, 30, 61, 0.82);
  color: #fff;
  border-left: 4px solid #60a5fa;
}

.clip-template-editor-fields {
  padding: 0 8px 0 0;
  border: 0;
  background: transparent;
  max-height: calc(100vh - 150px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.55) transparent;
}

.clip-template-editor-fields::-webkit-scrollbar,
.clip-template-library-v2::-webkit-scrollbar {
  width: 8px;
}

.clip-template-editor-fields::-webkit-scrollbar-track,
.clip-template-library-v2::-webkit-scrollbar-track {
  background: transparent;
}

.clip-template-editor-fields::-webkit-scrollbar-thumb,
.clip-template-library-v2::-webkit-scrollbar-thumb {
  border: 2px solid transparent;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.5);
  background-clip: padding-box;
}

.clip-template-editor-fields::-webkit-scrollbar-thumb:hover,
.clip-template-library-v2::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.62);
  background-clip: padding-box;
}

.clip-template-section + .clip-template-section {
  margin-top: 14px;
}

.clip-template-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.clip-template-section-head strong {
  color: #0f172a;
  font-size: 15px;
}

.clip-template-section-head span {
  display: inline-flex;
  min-width: 42px;
  height: 24px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 800;
}

.clip-template-segmented,
.clip-template-slider-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.clip-template-segment {
  min-height: 54px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #fff;
  padding: 10px 12px;
  color: #0f172a;
  text-align: left;
  cursor: pointer;
}

.clip-template-segment.active {
  border-color: rgba(59, 130, 246, 0.45);
  background: #f6f9ff;
}

.clip-template-segment strong,
.clip-template-segment span {
  display: block;
}

.clip-template-segment strong {
  margin-bottom: 4px;
  font-size: 13px;
}

.clip-template-segment span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.clip-template-slider-grid {
  margin-top: 12px;
}

.clip-template-slider-grid--single {
  grid-template-columns: minmax(0, 1fr);
}

.clip-template-slider,
.clip-template-toggle-card {
  display: flex;
  min-height: 76px;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #fff;
  padding: 12px;
}

.clip-template-slider span,
.clip-template-toggle-card > span {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.clip-template-slider input[type="range"] {
  width: 100%;
}

.clip-template-toggle-card {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.clip-template-asset-row {
  display: flex;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #fff;
  padding: 8px 10px 8px 14px;
  color: #64748b;
  font-size: 13px;
}

.clip-template-asset-row > div {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.template-bgm-thumb {
  background: linear-gradient(135deg, #d7e5ff 0%, #8eaef0 100%);
}

.toggle-switch__thumb {
  position: absolute;
  border-radius: 999px;
  background: #fff;
  transition: transform 0.18s ease;
}

.toggle-switch.clip-toggle-switch {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  width: 42px;
  height: 26px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: #dbe7fb;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18);
  cursor: pointer;
  flex: 0 0 auto;
  appearance: none;
  box-sizing: border-box;
}

.toggle-switch.clip-toggle-switch.active {
  background: #2f6df6;
}

.toggle-switch.clip-toggle-switch .toggle-switch__thumb {
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.18);
}

.toggle-switch.clip-toggle-switch.active .toggle-switch__thumb {
  transform: translateX(16px);
}

.toggle-switch.clip-toggle-switch:focus-visible {
  outline: 2px solid rgba(47, 109, 246, 0.28);
  outline-offset: 2px;
}

@media (max-width: 1280px) {
  .clip-template-library-v2 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .clip-template-editor-grid {
    grid-template-columns: 1fr;
  }

  .clip-template-cover-panel {
    position: static;
  }
}

@media (max-width: 1440px) {
  .grid-layout {
    grid-template-columns: repeat(2, minmax(320px, 1fr));
  }
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .grid-layout {
    grid-template-columns: 1fr;
  }

  .toolbar-grid,
  .toolbar-grid-3,
  .mini-grid,
  .choice-grid,
  .preview-meta,
  .background-choice-grid,
  .background-library-sections,
  .background-asset-grid,
  .clip-template-library-v2,
  .clip-template-segmented,
  .clip-template-slider-grid,
  .segmented-control {
    grid-template-columns: 1fr;
  }

  .inline-group,
  .edit-footer,
  .subtitle-card,
  .background-upload-bar,
  .clip-template-asset-row {
    flex-direction: column;
    align-items: stretch;
  }

  .clip-template-dialog-v2 {
    width: calc(100vw - 24px);
  }

  .clip-template-cover-tip {
    left: 50%;
    transform: translate(-50%, -50%);
  }
}
</style>
